from typing import Dict, List
from datetime import datetime, timedelta
import json

# Lazy import get_db to avoid circular import
def get_db():
    from main import get_db as _get_db
    return _get_db()

from app.models.asset_event import AssetEventType
from app.services.asset_event_service import AssetEventService


class InsightType:
    LOW_STOCK = 'low_stock'
    RESERVATION_CONFLICT = 'reservation_conflict'
    DEAD_STOCK = 'dead_stock'
    QUALITY_DROP = 'quality_drop'
    MISSING_EVIDENCE = 'missing_evidence'
    PRODUCTION_BOTTLENECK = 'production_bottleneck'
    SEASONAL_RISK = 'seasonal_risk'
    VALUATION_ANOMALY = 'valuation_anomaly'
    EXPIRING_RESERVATION = 'expiring_reservation'
    OVERDUE_MAINTENANCE = 'overdue_maintenance'


class AssetInsightsService:
    """Rule-based insight engine pro Asset Core."""
    
    @staticmethod
    def generate_all_insights() -> List[Dict]:
        """Generuje všechny insights."""
        insights = []
        
        insights.extend(AssetInsightsService.check_low_stock())
        insights.extend(AssetInsightsService.check_reservation_conflicts())
        insights.extend(AssetInsightsService.check_dead_stock())
        insights.extend(AssetInsightsService.check_quality_drops())
        insights.extend(AssetInsightsService.check_missing_evidence())
        insights.extend(AssetInsightsService.check_seasonal_risks())
        insights.extend(AssetInsightsService.check_expiring_reservations())
        
        # Sort by priority
        priority_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        insights.sort(key=lambda x: priority_order.get(x.get('severity', 'low'), 4))
        
        return insights
    
    @staticmethod
    def check_low_stock() -> List[Dict]:
        """
        LOW_STOCK: Dostupné množství < 20% celkového nebo < min_stock.
        """
        db = get_db()
        insights = []
        
        # Aggregate by type
        type_stats_rows = db.execute("""
            SELECT 
                at.id,
                at.name,
                at.code,
                COALESCE(SUM(al.quantity_total), 0) as total,
                COALESCE(SUM(al.quantity_available), 0) as available,
                COALESCE(SUM(al.quantity_reserved), 0) as reserved
            FROM asset_types at
            JOIN asset_lots al ON al.asset_type_id = at.id
            WHERE at.is_active = 1
            GROUP BY at.id
        """).fetchall()
        
        for ts_row in type_stats_rows:
            ts = dict(ts_row)
            total = ts.get('total', 0) or 0
            
            if total > 0:
                available = ts.get('available', 0) or 0
                available_pct = (available / total) * 100
                
                if available_pct < 10:
                    severity = 'critical'
                elif available_pct < 20:
                    severity = 'high'
                else:
                    continue
                
                insights.append({
                    'type': InsightType.LOW_STOCK,
                    'severity': severity,
                    'title': f'Nízký stav: {ts.get("name")}',
                    'description': f'Dostupné pouze {available} z {total} ks ({available_pct:.0f}%)',
                    'evidence': {
                        'type_id': ts.get('id'),
                        'type_code': ts.get('code'),
                        'total': total,
                        'available': available,
                        'reserved': ts.get('reserved', 0) or 0,
                        'available_percent': round(available_pct, 1)
                    },
                    'impact': 'Riziko nedostatku pro nadcházející zakázky',
                    'suggested_actions': [
                        {'action': 'order', 'label': 'Objednat', 'params': {'type_id': ts.get('id')}},
                        {'action': 'check_alternatives', 'label': 'Najít alternativy'}
                    ]
                })
        
        return insights
    
    @staticmethod
    def check_reservation_conflicts() -> List[Dict]:
        """
        RESERVATION_CONFLICT: Rezervace > dostupné množství.
        """
        db = get_db()
        insights = []
        
        # Find lots where reserved > available
        conflicts_rows = db.execute("""
            SELECT * FROM asset_lots 
            WHERE quantity_reserved > quantity_available
        """).fetchall()
        
        for lot_row in conflicts_rows:
            lot = dict(lot_row)
            shortage = (lot.get('quantity_reserved', 0) or 0) - (lot.get('quantity_available', 0) or 0)
            
            # Find affected reservations
            reservations_rows = db.execute("""
                SELECT * FROM asset_reservations 
                WHERE lot_id = ? AND status = 'active'
            """, (lot.get('id'),)).fetchall()
            
            type_row = None
            if lot.get('asset_type_id'):
                type_row = db.execute("SELECT name FROM asset_types WHERE id = ?", (lot['asset_type_id'],)).fetchone()
            
            type_name = type_row[0] if type_row else lot.get('lot_code', 'Unknown')
            
            insights.append({
                'type': InsightType.RESERVATION_CONFLICT,
                'severity': 'critical',
                'title': f'Konflikt rezervací: {type_name}',
                'description': f'Chybí {shortage} ks pro splnění rezervací',
                'evidence': {
                    'lot_id': lot.get('id'),
                    'available': lot.get('quantity_available', 0) or 0,
                    'reserved': lot.get('quantity_reserved', 0) or 0,
                    'shortage': shortage,
                    'reservations': [{'job_id': r['job_id'], 'quantity': r['quantity']} for r in reservations_rows]
                },
                'impact': f'Nelze splnit {len(reservations_rows)} rezervací',
                'suggested_actions': [
                    {'action': 'find_alternative_lots', 'label': 'Najít jiné šarže'},
                    {'action': 'adjust_reservations', 'label': 'Upravit rezervace'},
                    {'action': 'emergency_order', 'label': 'Urgentní objednávka'}
                ]
            })
        
        return insights
    
    @staticmethod
    def check_dead_stock() -> List[Dict]:
        """
        DEAD_STOCK: Položky bez pohybu > 6 měsíců nebo kvalita D.
        """
        db = get_db()
        insights = []
        six_months_ago = (datetime.utcnow() - timedelta(days=180)).isoformat()
        
        # Find lots without events in last 6 months
        lots_with_activity_rows = db.execute("""
            SELECT DISTINCT lot_id FROM asset_events 
            WHERE occurred_at >= ?
        """, (six_months_ago,)).fetchall()
        
        lots_with_activity = [r[0] for r in lots_with_activity_rows if r[0]]
        
        # Find dead lots
        query = "SELECT * FROM asset_lots WHERE quantity_total > 0"
        if lots_with_activity:
            placeholders = ','.join(['?'] * len(lots_with_activity))
            query += f" AND id NOT IN ({placeholders})"
            params = lots_with_activity
        else:
            params = []
        
        dead_lots_rows = db.execute(query, params).fetchall()
        
        # Also add quality D
        quality_d_rows = db.execute("""
            SELECT * FROM asset_lots 
            WHERE quantity_total > 0 AND quality_grade = 'D'
        """).fetchall()
        
        seen_ids = set()
        for lot_row in dead_lots_rows + quality_d_rows:
            lot = dict(lot_row)
            lot_id = lot.get('id')
            
            if lot_id in seen_ids:
                continue
            seen_ids.add(lot_id)
            
            value = (lot.get('quantity_total', 0) or 0) * float(lot.get('current_value_per_unit', 0) or 0)
            
            type_row = None
            if lot.get('asset_type_id'):
                type_row = db.execute("SELECT name FROM asset_types WHERE id = ?", (lot['asset_type_id'],)).fetchone()
            
            type_name = type_row[0] if type_row else lot.get('lot_code', 'Unknown')
            
            insights.append({
                'type': InsightType.DEAD_STOCK,
                'severity': 'medium' if value < 5000 else 'high',
                'title': f'Neprodejné zásoby: {type_name}',
                'description': f'{lot.get("quantity_total", 0)} ks bez pohybu nebo nízká kvalita',
                'evidence': {
                    'lot_id': lot_id,
                    'quantity': lot.get('quantity_total', 0) or 0,
                    'quality_grade': lot.get('quality_grade'),
                    'value': value,
                    'last_activity': lot.get('updated_at')
                },
                'impact': f'Vázaná hodnota: {value:,.0f} Kč',
                'suggested_actions': [
                    {'action': 'discount_sale', 'label': 'Sleva/výprodej'},
                    {'action': 'dispose', 'label': 'Likvidace'},
                    {'action': 'quality_review', 'label': 'Přehodnotit kvalitu'}
                ]
            })
        
        return insights
    
    @staticmethod
    def check_quality_drops() -> List[Dict]:
        """
        QUALITY_DROP: Pokles kvality za poslední měsíc.
        """
        db = get_db()
        insights = []
        month_ago = (datetime.utcnow() - timedelta(days=30)).isoformat()
        
        quality_events_rows = db.execute("""
            SELECT * FROM asset_events 
            WHERE event_type = ? AND occurred_at >= ?
        """, (AssetEventType.QUALITY_CHANGED, month_ago)).fetchall()
        
        for event_row in quality_events_rows:
            event = dict(event_row)
            payload_str = event.get('payload', '{}')
            
            try:
                payload = json.loads(payload_str) if isinstance(payload_str, str) else payload_str
            except:
                payload = {}
            
            old_grade = payload.get('previous_grade', 'A')
            new_grade = payload.get('new_grade', 'A')
            
            grade_values = {'A': 4, 'B': 3, 'C': 2, 'D': 1}
            if grade_values.get(new_grade, 0) < grade_values.get(old_grade, 0):
                lot_id = event.get('lot_id')
                if lot_id:
                    lot_row = db.execute("SELECT * FROM asset_lots WHERE id = ?", (lot_id,)).fetchone()
                    if lot_row:
                        lot = dict(lot_row)
                        
                        type_row = None
                        if lot.get('asset_type_id'):
                            type_row = db.execute("SELECT name FROM asset_types WHERE id = ?", (lot['asset_type_id'],)).fetchone()
                        
                        type_name = type_row[0] if type_row else lot.get('lot_code', 'Unknown')
                        
                        insights.append({
                            'type': InsightType.QUALITY_DROP,
                            'severity': 'high' if new_grade in ['C', 'D'] else 'medium',
                            'title': f'Pokles kvality: {type_name}',
                            'description': f'Kvalita klesla z {old_grade} na {new_grade}',
                            'evidence': {
                                'lot_id': lot_id,
                                'previous_grade': old_grade,
                                'new_grade': new_grade,
                                'reason': payload.get('reason'),
                                'quantity_affected': lot.get('quantity_total', 0) or 0
                            },
                            'impact': 'Snížená prodejní hodnota',
                            'suggested_actions': [
                                {'action': 'investigate', 'label': 'Zjistit příčinu'},
                                {'action': 'treatment', 'label': 'Ošetření'},
                                {'action': 'relocate', 'label': 'Přesunout do lepších podmínek'}
                            ]
                        })
        
        return insights
    
    @staticmethod
    def check_missing_evidence() -> List[Dict]:
        """
        MISSING_EVIDENCE: Loty bez foto dokumentace.
        """
        db = get_db()
        insights = []
        
        # Find lots without PHOTO_ADDED event
        lots_with_photo_rows = db.execute("""
            SELECT DISTINCT lot_id FROM asset_events 
            WHERE event_type = ?
        """, (AssetEventType.PHOTO_ADDED,)).fetchall()
        
        lots_with_photo = [r[0] for r in lots_with_photo_rows if r[0]]
        
        # Find lots without photos
        query = "SELECT * FROM asset_lots WHERE quantity_total > 0"
        if lots_with_photo:
            placeholders = ','.join(['?'] * len(lots_with_photo))
            query += f" AND id NOT IN ({placeholders})"
            params = lots_with_photo
        else:
            params = []
        
        query += " LIMIT 20"
        lots_without_rows = db.execute(query, params).fetchall()
        
        if lots_without_rows:
            sample_lots = []
            for lot_row in lots_without_rows[:5]:
                lot = dict(lot_row)
                type_row = None
                if lot.get('asset_type_id'):
                    type_row = db.execute("SELECT name FROM asset_types WHERE id = ?", (lot['asset_type_id'],)).fetchone()
                
                sample_lots.append({
                    'id': lot.get('id'),
                    'name': type_row[0] if type_row else lot.get('lot_code', 'Unknown')
                })
            
            insights.append({
                'type': InsightType.MISSING_EVIDENCE,
                'severity': 'low',
                'title': f'Chybí foto dokumentace ({len(lots_without_rows)} položek)',
                'description': 'Některé položky nemají foto evidenci',
                'evidence': {
                    'count': len(lots_without_rows),
                    'sample_lots': sample_lots
                },
                'impact': 'Horší přehled o stavu zásob',
                'suggested_actions': [
                    {'action': 'photo_campaign', 'label': 'Naplánovat focení'}
                ]
            })
        
        return insights
    
    @staticmethod
    def check_seasonal_risks() -> List[Dict]:
        """
        SEASONAL_RISK: Položky mimo sezónu prodeje.
        """
        db = get_db()
        insights = []
        current_month = datetime.utcnow().month
        
        # Find types outside sale season but with stock
        types_rows = db.execute("""
            SELECT * FROM asset_types 
            WHERE is_active = 1 
            AND sale_season_start IS NOT NULL 
            AND sale_season_end IS NOT NULL
        """).fetchall()
        
        for type_row in types_rows:
            t = dict(type_row)
            season_start = t.get('sale_season_start')
            season_end = t.get('sale_season_end')
            
            if not season_start or not season_end:
                continue
            
            # Is outside season?
            in_season = False
            if season_start <= season_end:
                in_season = season_start <= current_month <= season_end
            else:
                in_season = current_month >= season_start or current_month <= season_end
            
            if not in_season:
                # How much stock?
                total_row = db.execute("""
                    SELECT COALESCE(SUM(quantity_total), 0) 
                    FROM asset_lots 
                    WHERE asset_type_id = ?
                """, (t.get('id'),)).fetchone()
                
                total = total_row[0] if total_row else 0
                
                if total > 0:
                    insights.append({
                        'type': InsightType.SEASONAL_RISK,
                        'severity': 'medium',
                        'title': f'Mimo sezónu: {t.get("name")}',
                        'description': f'{total} ks mimo prodejní sezónu (sezóna: {season_start}-{season_end})',
                        'evidence': {
                            'type_id': t.get('id'),
                            'quantity': total,
                            'season_start': season_start,
                            'season_end': season_end,
                            'current_month': current_month
                        },
                        'impact': 'Riziko přezimování nebo ztráty',
                        'suggested_actions': [
                            {'action': 'winter_prep', 'label': 'Připravit na zimu'},
                            {'action': 'discount_sale', 'label': 'Výprodej'}
                        ]
                    })
        
        return insights
    
    @staticmethod
    def check_expiring_reservations() -> List[Dict]:
        """
        EXPIRING_RESERVATION: Rezervace blízko expiraci.
        """
        db = get_db()
        insights = []
        week_from_now = (datetime.utcnow() + timedelta(days=7)).isoformat()
        
        expiring_rows = db.execute("""
            SELECT * FROM asset_reservations 
            WHERE status = 'active' 
            AND expires_at IS NOT NULL 
            AND expires_at <= ?
        """, (week_from_now,)).fetchall()
        
        for res_row in expiring_rows:
            res = dict(res_row)
            expires_at_str = res.get('expires_at')
            
            try:
                expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
                days_left = (expires_at - datetime.utcnow()).days
            except:
                days_left = 0
            
            insights.append({
                'type': InsightType.EXPIRING_RESERVATION,
                'severity': 'high' if days_left <= 2 else 'medium',
                'title': 'Expirující rezervace',
                'description': f'Rezervace pro zakázku #{res.get("job_id")} vyprší za {days_left} dní',
                'evidence': {
                    'reservation_id': res.get('id'),
                    'job_id': res.get('job_id'),
                    'quantity': res.get('quantity', 0) or 0,
                    'expires_at': expires_at_str,
                    'days_left': days_left
                },
                'impact': 'Automatické uvolnění rezervace',
                'suggested_actions': [
                    {'action': 'extend_reservation', 'label': 'Prodloužit'},
                    {'action': 'fulfill_now', 'label': 'Vydat nyní'},
                    {'action': 'contact_job_manager', 'label': 'Kontaktovat vedoucího zakázky'}
                ]
            })
        
        return insights
