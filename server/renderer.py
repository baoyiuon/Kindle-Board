import os, sys, re
from datetime import datetime, timezone, timedelta
from PIL import Image, ImageDraw, ImageFont

CJK_FONT_PATHS = [
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    "C:/Windows/Fonts/msyh.ttc",
    "C:/Windows/Fonts/simhei.ttf"
]

PHONETIC_FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "C:/Windows/Fonts/arial.ttf",
    "C:/Windows/Fonts/segoeui.ttf",
    "C:/Windows/Fonts/msyh.ttc"
]

def get_font(size):
    for path in CJK_FONT_PATHS:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()

def get_phonetic_font(size):
    for path in PHONETIC_FONT_PATHS:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return get_font(size)

def clean_trans(trans_text):
    if not trans_text:
        return ""
    t = re.sub(r'（[^）]*）', '', trans_text)
    t = re.sub(r'\([^)]*\)', '', t)
    raw_parts = [p.strip() for p in re.split(r'[;；]', t) if p.strip()]
    if not raw_parts:
        raw_parts = [p.strip() for p in re.split(r'[,，]', t) if p.strip()]
    seen = set()
    parts = []
    for p in raw_parts:
        core = re.sub(r'^[a-z]+\.\s*', '', p)
        if core not in seen and core:
            seen.add(core)
            parts.append(p)
    if not parts:
        return trans_text.strip()[:24]
    return "；".join(parts[:2]).strip()

def render_dashboard(data, output_path=None):
    width, height = 1072, 1448
    img = Image.new("L", (width, height), 255)
    draw = ImageDraw.Draw(img)

    margin = 48
    usable_width = width - margin * 2

    # 字体设定（更大更清晰）
    font_date_big = get_font(60)
    font_section = get_font(34)
    
    # 单词卡片字体（英文超大号 56px，中文 34px）
    font_word = get_font(56)
    font_phonetic = get_phonetic_font(26)
    font_trans = get_font(34)
    
    # 待办事项字体（大字 40px）
    font_todo = get_font(40)
    font_small = get_font(24)

    # 1. 顶部日期（东八区北京时间，右上角完全留空）
    CST = timezone(timedelta(hours=8))
    now = datetime.now(CST)
    weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    date_str = f"{now.month}月{now.day}日 {weekdays[now.weekday()]}"
    
    draw.text((margin, 38), date_str, font=font_date_big, fill=0)
    draw.line([(margin, 115), (width - margin, 115)], fill=0, width=4)

    # 2. 生词模块（最多 6 个，双列紧凑排版，去除多余空隙）
    raw_words = data.get("words", [])
    words_to_show = raw_words[:6]

    y = 135
    draw.rectangle([(margin, y), (width - margin, y + 48)], fill=0)
    words_header = f"◆  今日重点生词 ({len(words_to_show)} / 6)"
    draw.text((margin + 20, y + 6), words_header, font=font_section, fill=255)
    y += 65

    col_w = 468
    col_gap = 40
    card_h = 152  # 紧凑高度，消灭大片空白
    row_gap = 14

    if not words_to_show:
        draw.text((margin + 25, y + 30), "暂无生词，可直接在手机端添加~", font=font_trans, fill=0)
        y_words_bottom = y + 80
    else:
        y_words_bottom = y
        for i, w_item in enumerate(words_to_show):
            row = i // 2
            col = i % 2
            x0 = margin + col * (col_w + col_gap)
            x1 = x0 + col_w
            y0 = y + row * (card_h + row_gap)
            y1 = y0 + card_h
            y_words_bottom = max(y_words_bottom, y1)

            # 卡片框（3px 加粗纯黑）
            draw.rounded_rectangle([(x0, y0), (x1, y1)], radius=12, outline=0, width=3)

            word = w_item.get("word", "").strip()
            phonetic = w_item.get("phonetic", "").strip()
            pos = w_item.get("pos", "").strip()
            trans = w_item.get("trans", "").strip()
            short_trans = clean_trans(f"{pos} {trans}".strip())

            # 第一行：大号英文单词（56px）
            draw.text((x0 + 18, y0 + 14), word, font=font_word, fill=0)
            w_bbox = draw.textbbox((x0 + 18, y0 + 14), word, font=font_word)
            word_w = w_bbox[2] - w_bbox[0]

            # 音标紧随单词右侧（若放得下）
            if phonetic:
                if (x0 + 18 + word_w + 12 + 180) < x1:
                    draw.text((x0 + 18 + word_w + 12, y0 + 38), phonetic, font=font_phonetic, fill=0)

            # 第二行：中文释义（紧贴单词下方，只隔 10~14px 间距，非常紧凑美观）
            max_text_w = col_w - 36
            while short_trans:
                t_bbox = draw.textbbox((0, 0), short_trans, font=font_trans)
                if (t_bbox[2] - t_bbox[0]) <= max_text_w:
                    break
                if "；" in short_trans:
                    short_trans = short_trans.split("；")[0].strip()
                elif len(short_trans) > 4:
                    short_trans = short_trans[:-2] + "..."
                    break
                else:
                    break

            draw.text((x0 + 18, y0 + 88), short_trans, font=font_trans, fill=0)

    # 3. 待办事项模块（放在底部，最多 5 条）
    y_todo_header = max(y_words_bottom + 35, 730)
    draw.rectangle([(margin, y_todo_header), (width - margin, y_todo_header + 48)], fill=0)
    
    todos = data.get("todos", [])
    undone_count = sum(1 for t in todos if not t.get("done", False))
    total_count = len(todos)
    todo_header = f"◆  待办事项清单  (待完成: {undone_count} / 总计: {total_count} · 最多展示 5 条)"
    draw.text((margin + 20, y_todo_header + 6), todo_header, font=font_section, fill=255)

    todo_box_top = y_todo_header + 60
    todo_box_bottom = 1365
    draw.rounded_rectangle([(margin, todo_box_top), (width - margin, todo_box_bottom)], radius=14, outline=0, width=3)

    if not todos:
        draw.text((margin + 35, todo_box_top + 40), "暂无待办事项，轻松度过今天吧~", font=font_todo, fill=0)
    else:
        sorted_todos = sorted(todos, key=lambda x: 1 if x.get("done", False) else 0)
        display_todos = sorted_todos[:5]
        
        # 均匀大字号排版
        item_y = todo_box_top + 26
        # 根据待办数量动态舒适间距
        item_gap = min(88, int((todo_box_bottom - todo_box_top - 50) / max(len(display_todos), 1)))

        for todo in display_todos:
            is_done = todo.get("done", False)
            text = todo.get("text", "")

            # 大号复选框（38x38）
            box_size = 38
            box_x = margin + 28
            box_y = item_y + 4
            draw.rectangle([(box_x, box_y), (box_x + box_size, box_y + box_size)], outline=0, width=3)

            if is_done:
                draw.line([(box_x + 6, box_y + 19), (box_x + 15, box_y + 30)], fill=0, width=5)
                draw.line([(box_x + 15, box_y + 30), (box_x + 32, box_y + 8)], fill=0, width=5)

            text_x = box_x + box_size + 22
            max_todo_w = usable_width - (text_x - margin) - 20
            todo_disp = text
            while todo_disp:
                tb = draw.textbbox((0, 0), todo_disp, font=font_todo)
                if (tb[2] - tb[0]) <= max_todo_w:
                    break
                todo_disp = todo_disp[:-2] + "..."

            draw.text((text_x, item_y), todo_disp, font=font_todo, fill=0)
            if is_done:
                tb = draw.textbbox((text_x, item_y), todo_disp, font=font_todo)
                strike_y = item_y + 24
                draw.line([(text_x, strike_y), (tb[2], strike_y)], fill=0, width=4)

            item_y += item_gap

    # 4. 底部时间戳（左侧）与 手机端便签标签（右侧右下角）
    draw.line([(margin, 1390), (width - margin, 1390)], fill=0, width=2)
    refresh_info = f"Kindle 同步更新于: {now.strftime('%Y-%m-%d %H:%M')}"
    draw.text((margin, 1405), refresh_info, font=font_small, fill=0)

    # 手机页面设置的标签内容放到底部右下角显示
    custom_note = data.get("note", "").strip()
    if custom_note:
        max_note_w = usable_width - 340 # 留出左侧时间戳空间
        note_disp = custom_note
        while note_disp:
            nb = draw.textbbox((0, 0), note_disp, font=font_small)
            if (nb[2] - nb[0]) <= max_note_w:
                break
            note_disp = note_disp[:-2] + "..."
        
        nb = draw.textbbox((0, 0), note_disp, font=font_small)
        nw = nb[2] - nb[0]
        draw.text((width - margin - nw, 1405), note_disp, font=font_small, fill=0)

    if output_path:
        img.save(output_path, "PNG", optimize=True)
    return img

if __name__ == "__main__":
    demo = {
        "note": "保持专注与热爱，每天进步一点点！",
        "words": [
            {"word": "car", "trans": "n. 汽车，轿车；<美>车厢"},
            {"word": "banana", "trans": "n. 香蕉；香蕉树"},
            {"word": "father", "trans": "n. 父亲，爸爸；祖先"},
            {"word": "home", "trans": "n. 家，住宅；房子，寓所"},
            {"word": "eat", "trans": "v. 吃，吃饭；侵蚀，损耗"},
            {"word": "tiger", "trans": "n. 老虎；凶暴的人"}
        ],
        "todos": [
            {"id": "1", "text": "早晨完成考研/雅思生词背诵 20 个", "done": False},
            {"id": "2", "text": "整理今晚阅读书单与洗漱", "done": False},
            {"id": "3", "text": "检查服务器运行状态与每日自动化备份", "done": True}
        ]
    }
    render_dashboard(demo, "test_dashboard.png")
    print("Rendered test_dashboard.png successfully!")