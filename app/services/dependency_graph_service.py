from typing import List, Dict, Optional
from datetime import datetime

# Lazy import get_db to avoid circular import
def get_db():
    from main import get_db as _get_db
    return _get_db()


class DependencyGraphService:
    
    @staticmethod
    def get_job_dependencies(job_id: int) -> List[dict]:
        """Vrátí všechny závislosti pro zakázku."""
        db = get_db()
        
        # Get all task IDs for this job
        task_ids_rows = db.execute("SELECT id FROM tasks WHERE job_id = ?", (job_id,)).fetchall()
        task_ids = [row[0] for row in task_ids_rows]
        
        if not task_ids:
            return []
        
        # Get dependencies where either predecessor or successor is in this job
        placeholders = ','.join(['?'] * len(task_ids))
        deps_rows = db.execute(f"""
            SELECT * FROM task_dependencies 
            WHERE predecessor_task_id IN ({placeholders}) 
            OR successor_task_id IN ({placeholders})
        """, task_ids + task_ids).fetchall()
        
        return [dict(dep) for dep in deps_rows]
    
    @staticmethod
    def build_adjacency_list(job_id: int) -> Dict[int, List[int]]:
        """Vytvoří adjacency list pro graf závislostí."""
        dependencies = DependencyGraphService.get_job_dependencies(job_id)
        adj_list = {}
        
        for dep in dependencies:
            pred_id = dep['predecessor_task_id']
            succ_id = dep['successor_task_id']
            
            if pred_id not in adj_list:
                adj_list[pred_id] = []
            adj_list[pred_id].append(succ_id)
        
        return adj_list
    
    @staticmethod
    def detect_cycles(job_id: int) -> List[List[int]]:
        """Detekuje cyklické závislosti."""
        adj_list = DependencyGraphService.build_adjacency_list(job_id)
        visited = set()
        rec_stack = set()
        cycles = []
        
        def dfs(node: int, path: List[int]) -> bool:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in adj_list.get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor, path):
                        return True
                elif neighbor in rec_stack:
                    cycle_start = path.index(neighbor)
                    cycles.append(path[cycle_start:] + [neighbor])
                    return True
            
            path.pop()
            rec_stack.remove(node)
            return False
        
        # Get all nodes
        all_nodes = set(adj_list.keys())
        dependencies = DependencyGraphService.get_job_dependencies(job_id)
        for dep in dependencies:
            all_nodes.add(dep['successor_task_id'])
        
        for node in all_nodes:
            if node not in visited:
                dfs(node, [])
        
        return cycles
    
    @staticmethod
    def topological_sort(job_id: int) -> Optional[List[int]]:
        """Topologické seřazení tasků."""
        if DependencyGraphService.detect_cycles(job_id):
            return None
        
        adj_list = DependencyGraphService.build_adjacency_list(job_id)
        in_degree = {}
        all_nodes = set()
        
        for pred, successors in adj_list.items():
            all_nodes.add(pred)
            if pred not in in_degree:
                in_degree[pred] = 0
            for succ in successors:
                all_nodes.add(succ)
                in_degree[succ] = in_degree.get(succ, 0) + 1
        
        queue = [node for node in all_nodes if in_degree.get(node, 0) == 0]
        result = []
        
        while queue:
            node = queue.pop(0)
            result.append(node)
            for neighbor in adj_list.get(node, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        return result if len(result) == len(all_nodes) else None
    
    @staticmethod
    def get_downstream_tasks(task_id: int, max_depth: int = None) -> List[Dict]:
        """Vrátí všechny tasky, které závisí na tomto tasku."""
        db = get_db()
        result = []
        visited = set()
        
        def traverse(tid: int, depth: int):
            if tid in visited or (max_depth and depth > max_depth):
                return
            visited.add(tid)
            
            deps_rows = db.execute(
                "SELECT * FROM task_dependencies WHERE predecessor_task_id = ?",
                (tid,)
            ).fetchall()
            
            for dep_row in deps_rows:
                dep = dict(dep_row)
                succ_id = dep['successor_task_id']
                
                succ_task_row = db.execute("SELECT * FROM tasks WHERE id = ?", (succ_id,)).fetchone()
                if succ_task_row:
                    succ_task = dict(succ_task_row)
                    result.append({
                        'task_id': succ_task['id'],
                        'title': succ_task.get('title', 'Unknown'),
                        'status': succ_task.get('status', 'planned'),
                        'depth': depth,
                        'dependency_type': dep['dependency_type'],
                        'is_critical': bool(dep.get('is_critical', False))
                    })
                    traverse(succ_id, depth + 1)
        
        traverse(task_id, 1)
        return result
    
    @staticmethod
    def get_upstream_tasks(task_id: int, max_depth: int = None) -> List[Dict]:
        """Vrátí všechny tasky, na kterých tento task závisí."""
        db = get_db()
        result = []
        visited = set()
        
        def traverse(tid: int, depth: int):
            if tid in visited or (max_depth and depth > max_depth):
                return
            visited.add(tid)
            
            deps_rows = db.execute(
                "SELECT * FROM task_dependencies WHERE successor_task_id = ?",
                (tid,)
            ).fetchall()
            
            for dep_row in deps_rows:
                dep = dict(dep_row)
                pred_id = dep['predecessor_task_id']
                
                pred_task_row = db.execute("SELECT * FROM tasks WHERE id = ?", (pred_id,)).fetchone()
                if pred_task_row:
                    pred_task = dict(pred_task_row)
                    result.append({
                        'task_id': pred_task['id'],
                        'title': pred_task.get('title', 'Unknown'),
                        'status': pred_task.get('status', 'planned'),
                        'depth': depth,
                        'is_satisfied': dep.get('status') == 'satisfied'
                    })
                    traverse(pred_id, depth + 1)
        
        traverse(task_id, 1)
        return result
    
    @staticmethod
    def check_can_start(task_id: int) -> Dict:
        """Kontroluje, zda task může být zahájen."""
        db = get_db()
        
        deps_rows = db.execute("""
            SELECT * FROM task_dependencies 
            WHERE successor_task_id = ? AND is_hard = 1
        """, (task_id,)).fetchall()
        
        blocking = []
        for dep_row in deps_rows:
            dep = dict(dep_row)
            if dep.get('status') != 'satisfied':
                pred_id = dep['predecessor_task_id']
                pred_task_row = db.execute("SELECT * FROM tasks WHERE id = ?", (pred_id,)).fetchone()
                
                if pred_task_row:
                    pred_task = dict(pred_task_row)
                    blocking.append({
                        'dependency_id': dep['id'],
                        'predecessor_task_id': pred_id,
                        'predecessor_title': pred_task.get('title', 'Unknown'),
                        'predecessor_status': pred_task.get('status', 'planned')
                    })
        
        return {
            'can_start': len(blocking) == 0,
            'blocking_dependencies': blocking,
            'total_dependencies': len(deps_rows),
            'satisfied_count': len(deps_rows) - len(blocking)
        }
    
    @staticmethod
    def update_dependency_status(dependency_id: int) -> dict:
        """Aktualizuje status závislosti."""
        db = get_db()
        
        dep_row = db.execute("SELECT * FROM task_dependencies WHERE id = ?", (dependency_id,)).fetchone()
        if not dep_row:
            return None
        
        dep = dict(dep_row)
        pred_id = dep['predecessor_task_id']
        
        pred_task_row = db.execute("SELECT * FROM tasks WHERE id = ?", (pred_id,)).fetchone()
        if not pred_task_row:
            return dep
        
        pred_task = dict(pred_task_row)
        dep_type = dep['dependency_type']
        new_status = dep['status']
        satisfied_at = None
        violated_at = None
        
        if dep_type == 'finish_to_start':
            if pred_task.get('status') == 'completed':
                new_status = 'satisfied'
                satisfied_at = datetime.utcnow().isoformat()
            elif pred_task.get('status') == 'failed':
                new_status = 'violated'
                violated_at = datetime.utcnow().isoformat()
            elif pred_task.get('status') == 'in_progress':
                new_status = 'active'
        
        # Update dependency
        db.execute("""
            UPDATE task_dependencies 
            SET status = ?, satisfied_at = ?, violated_at = ?
            WHERE id = ?
        """, (new_status, satisfied_at, violated_at, dependency_id))
        db.commit()
        
        # Return updated dependency
        updated_dep = db.execute("SELECT * FROM task_dependencies WHERE id = ?", (dependency_id,)).fetchone()
        return dict(updated_dep) if updated_dep else None
