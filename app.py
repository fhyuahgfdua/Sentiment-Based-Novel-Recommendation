from flask import Flask, request, jsonify
import torch
from transformers import BertTokenizer, BertForSequenceClassification
from flask_cors import CORS
import pymysql

app = Flask(__name__)
CORS(app)
app.config['JSON_AS_ASCII'] = False

# 数据库配置
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "root",  # 改成你自己的密码
    "database": "novel_db",
    "charset": "utf8mb4"
}

# 模型配置
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
MODEL_PATH = "./sentiment_model"

tokenizer = BertTokenizer.from_pretrained(MODEL_PATH)
model = BertForSequenceClassification.from_pretrained(MODEL_PATH).to(DEVICE)
model.eval()

ID2EMO = {0: "中性", 1: "吐槽", 2: "虐点", 3: "爽点"}
EMO2TAG = {"中性": "中性文", "吐槽": "吐槽文", "虐点": "虐文", "爽点": "爽文"}

# 预测
def predict_emotion(text):
    inputs = tokenizer(text, return_tensors="pt", max_length=128, padding=True, truncation=True).to(DEVICE)
    with torch.no_grad():
        outputs = model(**inputs)
    return ID2EMO[torch.argmax(outputs.logits, dim=1).item()]

# 查询书籍
def get_books_by_tag(tag):
    try:
        conn = pymysql.connect(**DB_CONFIG)
        cur = conn.cursor(pymysql.cursors.DictCursor)
        cur.execute("SELECT title, author, tag FROM novel WHERE tag = %s", (tag,))
        books = cur.fetchall()
        cur.close()
        conn.close()
        return books
    except:
        return []

# 直接返回前端页面（彻底解决 Jinja2 冲突！）
@app.route('/')
def index():
    return '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <title>情感分析+书籍推荐</title>
  <script src="https://cdn.jsdelivr.net/npm/vue@3/dist/vue.global.js"></script>
</head>
<body>
  <div id="app">
    <h2>小说评论情感分析</h2>
    <textarea v-model="text" rows="6" cols="60"></textarea>
    <br><br>
    <button @click="analyze">分析情感</button>
    <h3>情感结果：{{ emotion }}</h3>
    <h4>推荐书籍：</h4>
    <ul>
      <li v-for="book in books">{{ book.title }} - {{ book.author }} ({{ book.tag }})</li>
    </ul>
  </div>

  <script>
    const { createApp } = Vue
    createApp({
      data() {
        return { text: "", emotion: "", books: [] }
      },
      methods: {
        async analyze() {
          const res = await fetch("/api/analyze", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text: this.text })
          })
          const data = await res.json()
          this.emotion = data.emotion
          this.books = data.books
        }
      }
    }).mount("#app")
  </script>
</body>
</html>
    '''

# 接口
@app.route("/api/analyze", methods=["POST"])
def analyze():
    text = request.json.get("text", "")
    emotion = predict_emotion(text)
    tag = EMO2TAG[emotion]
    books = get_books_by_tag(tag)
    return jsonify({"emotion": emotion, "books": books})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
