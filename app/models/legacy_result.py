"""
Legacy MySQL 5.6 数据库模型示例
用于从低版本数据库查询订单结果数据
"""
from app.extensions import db


class LegacyOrderResult(db.Model):
    """低版本数据库中的订单结果表（示例）"""
    __bind_key__ = 'legacy_mysql'
    __tablename__ = 'order_results'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, nullable=False, index=True)
    result_data = db.Column(db.Text)
    status = db.Column(db.String(50))
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime)

    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'result_data': self.result_data,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
