from typing import Dict, List


class AIExplainabilityService:
    """
    Každé AI rozhodnutí MUSÍ být vysvětlitelné.
    Tato služba generuje lidsky čitelná vysvětlení.
    """
    
    @staticmethod
    def explain_bottleneck_detection(bottleneck: Dict) -> Dict:
        """
        Vysvětlí proč byl detekován bottleneck.
        """
        explanation = {
            'summary': '',
            'evidence': [],
            'confidence': 0.0,
            'methodology': ''
        }
        
        bn_type = bottleneck.get('type')
        
        if bn_type == 'resource':
            explanation['summary'] = f"Detected employee overload based on active task count"
            explanation['evidence'] = [
                f"Employee has {bottleneck.get('detail', 'multiple')} active tasks",
                "Threshold for overload is 5+ concurrent tasks",
                "Historical data shows quality drops when exceeding this threshold"
            ]
            explanation['confidence'] = 0.85
            explanation['methodology'] = "Task count analysis with configurable thresholds"
        
        elif bn_type == 'dependency':
            explanation['summary'] = f"Task identified as critical bottleneck in dependency chain"
            explanation['evidence'] = [
                f"Task blocks {bottleneck.get('detail', 'multiple other')} tasks",
                "Delay in this task will cascade downstream",
                "Graph analysis confirmed critical path position"
            ]
            explanation['confidence'] = 0.90
            explanation['methodology'] = "Dependency graph traversal and critical path analysis"
        
        elif bn_type == 'material':
            explanation['summary'] = "Material shortage blocking work progress"
            explanation['evidence'] = [
                "Task explicitly blocked with material shortage reason",
                "Blocking event recorded in system",
                "No alternative materials available"
            ]
            explanation['confidence'] = 0.95
            explanation['methodology'] = "Event analysis and material availability check"
        
        return explanation
    
    @staticmethod
    def explain_pattern_detection(pattern: Dict) -> Dict:
        """
        Vysvětlí detekovaný vzorec.
        """
        return {
            'summary': f"Pattern '{pattern['reason']}' detected with {pattern['occurrence_count']} occurrences",
            'evidence': [
                f"Found in {pattern['affected_tasks']} different tasks",
                f"Total impact: {pattern['total_impact_hours']} hours",
                f"Sample tasks: {', '.join(map(str, pattern['sample_task_ids'][:3]))}"
            ],
            'confidence': pattern['confidence'],
            'methodology': "Historical event aggregation and frequency analysis",
            'limitations': [
                "Pattern may be coincidental if occurrence count is low",
                "Causal relationship not proven, only correlation"
            ]
        }
    
    @staticmethod
    def explain_recommendation(recommendation: Dict, context: Dict) -> Dict:
        """
        Vysvětlí proč AI doporučuje konkrétní akci.
        """
        return {
            'recommendation': recommendation.get('action') or recommendation.get('recommendation'),
            'reasoning': [
                f"Based on analysis of {context.get('data_points', 'available')} data points",
                f"Historical success rate of similar action: {context.get('success_rate', 'unknown')}",
                f"Expected improvement: {recommendation.get('expected_improvement', 'positive')}"
            ],
            'confidence': recommendation.get('confidence', 0.7),
            'alternatives': context.get('alternatives', []),
            'risks': context.get('risks', ['Recommendation based on limited data']),
            'human_review_suggested': recommendation.get('confidence', 0.7) < 0.8
        }
