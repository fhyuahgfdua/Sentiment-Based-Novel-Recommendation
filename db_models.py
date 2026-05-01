from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# 1. 用户表
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False) # 实际项目中应加密存储
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<User {self.username}>'

# 2. 小说表
class Novel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100))
    description = db.Column(db.Text)
    cover_url = db.Column(db.String(255)) # 封面图链接
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # 关联评论（一对多）
    comments = db.relationship('Comment', backref='novel', lazy=True)

    def __repr__(self):
        return f'<Novel {self.title}>'

# 3. 评论表
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    sentiment = db.Column(db.String(50)) # 情感标签：爽点/虐点/吐槽/中性
    score = db.Column(db.Float) # 情感置信度分数
    novel_id = db.Column(db.Integer, db.ForeignKey('novel.id'), nullable=False) # 外键
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Comment {self.content[:20]}...>'
