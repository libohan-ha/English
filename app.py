import os
from flask import Flask, render_template, request
from flask_caching import Cache
import markdown2
import glob
import re

app = Flask(__name__)
app.config['CACHE_TYPE'] = 'simple'
cache = Cache(app)

STORIES_PER_PAGE = 10
CACHE_TIMEOUT = 300

def process_content(content):
    # 分离正文和单词解释
    parts = content.split('单词解释：')
    story_text = parts[0]
    definitions = parts[1] if len(parts) > 1 else ''
    
    # 获取所有需要高亮的单词
    words = []
    for line in definitions.split('\n'):
        if line.strip():  # 确保行不为空
            # 尝试提取单词（忽略序号和空格）
            if '：' in line:
                word = line.split('：')[0].strip()
                # 移除序号（如果有的话）
                word = re.sub(r'^\d+\.\s*', '', word)
                if word:
                    words.append(word)
    
    # 在正文中高亮单词
    for word in words:
        # 使用零宽断言确保匹配完整单词
        pattern = re.compile(f'(?<![a-zA-Z]){re.escape(word)}(?![a-zA-Z])')
        story_text = pattern.sub(f'<span class="highlight">{word}</span>', story_text)
    
    # 格式化单词解释
    formatted_definitions = '<ul class="word-definitions">'
    for line in definitions.split('\n'):
        if line.strip() and '：' in line:
            word = line.split('：')[0].strip()
            word = re.sub(r'^\d+\.\s*', '', word)  # 移除序号
            definition = line.split('：', 1)[1]
            formatted_definitions += f'<li><span class="word">{word}</span>：{definition.strip()}</li>'
    formatted_definitions += '</ul>'
    
    return story_text, formatted_definitions

def get_all_stories():
    cache_key = 'all_stories'
    stories = cache.get(cache_key)
    
    if stories is not None:
        return stories
        
    stories = []
    story_dir = os.path.join(os.path.dirname(__file__), 'stories')
    story_files = glob.glob(os.path.join(story_dir, 'story_*.md'))
    story_files.sort(key=lambda x: int(os.path.basename(x).split('_')[1].split('.')[0]))
    
    for file in story_files:
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read()
            story_text, definitions = process_content(content)
            story_id = int(os.path.basename(file).split('_')[1].split('.')[0])
            
            stories.append({
                'id': story_id,
                'content': story_text,
                'definitions': definitions,
                'preview': re.sub(r'<[^>]+>', '', story_text)[:200],
            })
    
    cache.set(cache_key, stories, timeout=CACHE_TIMEOUT)
    return stories

@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('q', '').strip()
    
    stories = get_all_stories()
    
    if search_query:
        stories = [s for s in stories if search_query.lower() in s['content'].lower()]
    
    total_stories = len(stories)
    total_pages = (total_stories + STORIES_PER_PAGE - 1) // STORIES_PER_PAGE
    
    start = (page - 1) * STORIES_PER_PAGE
    end = start + STORIES_PER_PAGE
    paginated_stories = stories[start:end]
    
    return render_template('index.html',
                         stories=paginated_stories,
                         current_page=page,
                         total_pages=total_pages,
                         search_query=search_query)

@app.route('/story/<int:story_id>')
def story(story_id):
    stories = get_all_stories()
    story = next((s for s in stories if s['id'] == story_id), None)
    if story is None:
        return "Story not found", 404
    
    # 找到上一篇和下一篇
    story_ids = [s['id'] for s in stories]
    current_index = story_ids.index(story_id)
    prev_story = stories[current_index - 1] if current_index > 0 else None
    next_story = stories[current_index + 1] if current_index < len(stories) - 1 else None
        
    return render_template('story.html', 
                         story=story,
                         prev_story=prev_story,
                         next_story=next_story)

if __name__ == '__main__':
    app.run(debug=True, port=9000) 