from datetime import datetime

QUOTA_PER_DAY = 100  # Modifie cette valeur selon ta politique

def today_range():
    now = datetime.utcnow()
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = now.replace(hour=23, minute=59, second=59, microsecond=999999)
    return start, end

def quota_remaining(db, user_id):
    from app.models.translation import Translation
    start, end = today_range()
    count = db.query(Translation).filter(
        Translation.user_id == user_id,
        Translation.created_at >= start,
        Translation.created_at <= end
    ).count()
    return max(0, QUOTA_PER_DAY - count), count

