from app.models import db

def db_exec_one(query):
    return db.session.execute(query).scalar_one()

def db_exec_one_optional(klass, **kwargs):
    select = db.select(klass)
    if len(kwargs) > 0:
        select = select.filter_by(**kwargs)

    result = db.session.execute(select).one_or_none()
    if result:
        return result[0]
    else:
        return None

def db_exec_all(klass, **kwargs):
    select = db.select(klass)
    limit = kwargs.pop('limit', None)
    order_by = kwargs.pop('order_by', None)
    if len(kwargs) > 0:
        select = select.filter_by(**kwargs)
    if order_by:
        select = select.order_by(order_by)
    if limit:
        select = select.limit(limit)

    return db.session.execute(select).scalars().all()

def db_exec_by_id(klass, id):
    return db.session.get(klass, id)

def db_exec_first(klass, **kwargs):
    kwargs['limit'] = 1
    results = db_exec_all(klass, **kwargs)
    if len(results) > 0:
        return results[0]
    else:
        return None

def db_count(klass, **kwargs):
    select = db.select(db.func.count()).select_from(klass)
    if len(kwargs) > 0:
        select = select.filter_by(**kwargs)

    return db.session.execute(db.session.scalar(select))

def db_delete(klass, **kwargs):
    if len(kwargs) == 0:
        raise Exception("Delete attempt without specifying a query - mistake?")
    return db.session.execute(db.delete(klass).filter_by(**kwargs)).rowcount

def db_delete_all(klass):
    return db.session.execute(db.delete(klass)).rowcount
