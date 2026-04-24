with open('index.html', 'r') as f:
    content = f.read()

# Fix layout height and overflow
content = content.replace(
    'height:100vh;position:relative;z-index:1}',
    'height:100vh;position:relative;z-index:1;overflow:hidden}'
)
content = content.replace(
    'main{display:flex;flex-direction:column;overflow:hidden}',
    'main{display:flex;flex-direction:column;overflow:hidden;min-height:0;height:100%}'
)
content = content.replace(
    '#chat-container{flex:1;overflow-y:auto;',
    '#chat-container{flex:1;overflow-y:auto;min-height:0;'
)

with open('index.html', 'w') as f:
    f.write(content)
print("Fixed!")
