import os
import html
import json
import sys
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            if self._pageNumber > 1:
                self.draw_page_number(num_pages)
            super().showPage()
        super().save()

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#7f8c8d"))
        page_text = f"Страница {self._pageNumber} из {page_count}"

        # ИСПРАВЛЕНО: используем letter[0] для получения числового значения ширины
        page_width = letter[0]
        self.drawRightString(page_width - 54, 36, page_text)

        # Линия над футером
        self.setStrokeColor(colors.HexColor("#bdc3c7"))
        self.setLineWidth(0.5)
        self.line(54, 50, page_width - 54, 50)
        self.restoreState()


def get_project_mapping(root_directory, ignored_names):
    print("[1/4] Сканирование структуры директорий...")
    mapping = {}
    for dirpath, dirnames, filenames in os.walk(root_directory):
        dirnames[:] = [d for d in dirnames if d not in ignored_names]
        py_files = [f for f in sorted(filenames) if f.endswith('.py') and f not in ignored_names]

        if py_files:
            rel_path = os.path.relpath(dirpath, root_directory)
            mapping[rel_path] = py_files
    return mapping


def read_file_safely(full_path):
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            return f.read(), True
    except UnicodeDecodeError:
        try:
            with open(full_path, 'r', encoding='cp1251') as f:
                return f.read(), True
        except Exception as e:
            return f"# [Критическая ошибка кодировки при чтении файла: {e}]", False
    except Exception as e:
        return f"# [Ошибка доступа к файлу: {e}]", False


def build_json_archive(root_directory, project_map, output_json_path, total_files):
    print(f"[2/4] Формирование JSON дампа для {total_files} файлов...")
    json_tree = {}
    processed = 0

    for rel_path, filenames in project_map.items():
        current_dir_dict = json_tree

        if rel_path != ".":
            for part in rel_path.split(os.sep):
                if part not in current_dir_dict:
                    current_dir_dict[part] = {}
                current_dir_dict = current_dir_dict[part]

        for filename in filenames:
            actual_dir = root_directory if rel_path == "." else os.path.join(root_directory, rel_path)
            full_path = os.path.join(actual_dir, filename)
            display_name = os.path.join(rel_path, filename) if rel_path != "." else filename

            processed += 1
            print(f" -> [JSON {processed}/{total_files}] Обработка: {display_name}", end='\r')

            content, success = read_file_safely(full_path)
            if not success:
                print(f"\n[ВНИМАНИЕ JSON]: Ошибка листинга файла: {display_name}")

            current_dir_dict[filename] = content

    print("\n Запись структуры в project_dump.json...")
    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(json_tree, f, ensure_ascii=False, indent=2)
    print(f" Успешно сохранен JSON: {output_json_path}")


def build_pdf_archive(root_directory, project_map, output_pdf_path, total_files):
    print(f"[3/4] Подготовка структуры PDF и таблицы статистики...")
    styles = getSampleStyleSheet()

    code_style = ParagraphStyle('CodeStyle', parent=styles['Normal'], fontName='Courier', fontSize=7.5, leading=9.5,
                                whitespace='preserve')
    title_style = ParagraphStyle('FileTitleStyle', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=11,
                                 leading=14, spaceBefore=4, spaceAfter=8)
    stat_header_style = ParagraphStyle('StatHeader', fontName='Helvetica-Bold', fontSize=14, leading=18, spaceBefore=10,
                                       spaceAfter=15, alignment=1)
    table_cell_style = ParagraphStyle('TableCell', fontName='Helvetica', fontSize=9, leading=11)
    table_cell_bold = ParagraphStyle('TableCellBold', fontName='Helvetica-Bold', fontSize=9, leading=11)

    pdf_elements = []

    pdf_elements.append(Paragraph("СТАТИСТИКА ИСХОДНОГО КОДА ПРОЕКТА", stat_header_style))
    pdf_elements.append(Spacer(1, 10))

    # Рассчитываем ширину колонок на основе ширины страницы letter[0]
    page_width = letter[0]
    available_width = page_width - 108  # вычитаем левое и правое поля (54 * 2)
    col_widths = [available_width * 0.75, available_width * 0.25]

    table_data = [[Paragraph("<b>Относительный путь к каталогу</b>", table_cell_bold),
                   Paragraph("<b>Кол-во .py файлов</b>", table_cell_bold)]]

    for rel_path, filenames in project_map.items():
        display_path = "[Корень проекта]" if rel_path == "." else rel_path
        table_data.append([Paragraph(display_path, table_cell_style), Paragraph(str(len(filenames)), table_cell_style)])

    table_data.append(
        [Paragraph("<b>ИТОГО:</b>", table_cell_bold), Paragraph(f"<b>{total_files}</b>", table_cell_bold)])

    stat_table = Table(table_data, colWidths=col_widths)
    stat_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.HexColor("#2c3e50")),
        ('TEXTCOLOR', (0, 0), (1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.HexColor("#f8f9fa"), colors.white]),
        ('LINEBELOW', (0, -1), (-1, -1), 1.5, colors.HexColor("#2c3e50")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#bdc3c7")),
    ]))
    pdf_elements.append(stat_table)
    pdf_elements.append(PageBreak())

    print(f"[4/4] Добавление листингов кода в PDF элементы...")
    pdf_success_counter = 0

    for rel_path, filenames in project_map.items():
        actual_dir = root_directory if rel_path == "." else os.path.join(root_directory, rel_path)

        for filename in filenames:
            full_path = os.path.join(actual_dir, filename)
            display_name = os.path.join(rel_path, filename) if rel_path != "." else filename

            pdf_success_counter += 1
            print(f" -> [PDF {pdf_success_counter}/{total_files}] Компиляция: {display_name}", end='\r')

            try:
                code_content, _ = read_file_safely(full_path)

                if len(pdf_elements) > 2:
                    pdf_elements.append(PageBreak())

                pdf_elements.append(Paragraph(f"Файл: {display_name}", title_style))

                escaped_code = html.escape(code_content)
                formatted_code = escaped_code.replace('\n', '<br/>').replace(' ', '&nbsp;')

                pdf_elements.append(Paragraph(formatted_code, code_style))

            except Exception as pdf_error:
                print(f"\n[ОШИБКА PDF]: Не удалось добавить {display_name}. Причина: {pdf_error}")

    print("\n Сборка финального PDF-документа (генерация страниц)...")
    doc = SimpleDocTemplate(output_pdf_path, pagesize=letter, leftMargin=54, rightMargin=54, topMargin=54,
                            bottomMargin=64)
    doc.build(pdf_elements, canvasmaker=NumberedCanvas)

    print("-" * 60)
    if pdf_success_counter != total_files:
        print(f"Ошибка самопроверки! Найдено файлов: {total_files}, записано: {pdf_success_counter}")
    else:
        print(f"Все проверки успешны! Скомпилировано файлов в PDF: {pdf_success_counter}")
    print(f"Успешно записан PDF: {output_pdf_path}")


def main():
    ignored_names = {
        '__pycache__', '.git', '.svn', '.hg', '.idea', '.vscode',
        'node_modules', 'venv', 'env', '.venv', '.env', 'virtualenv',
        'dist', 'build', '.mypy_cache', '.pytest_cache', '.tox',
        '.ipynb_checkpoints', '.DS_Store', 'Thumbs.db', '.trash', '.tmp',
        'logs', 'backup', 'old'
    }

    target_dir = "/home/sergey/Documents/configurate"
    output_pdf = "/home/sergey/Documents/configurate_archive.pdf"
    output_json = "/home/sergey/Documents/project_dump.json"

    print("=== ЗАПУСК АРХИВАЦИИ ПРОЕКТА ===")
    project_map = get_project_mapping(target_dir, ignored_names)
    total_py_files = sum(len(files) for files in project_map.values())

    if total_py_files == 0:
        print(f"В папке {target_dir} не найдено .py файлов.")
        return

    print(f"Карта построена. Обнаружено папок с кодом: {len(project_map)}, всего файлов .py: {total_py_files}")
    print("-" * 60)

    build_json_archive(target_dir, project_map, output_json, total_py_files)
    print("-" * 60)

    build_pdf_archive(target_dir, project_map, output_pdf, total_py_files)
    print("=== ПРОЦЕСС ЗАВЕРШЕН ===")


if __name__ == "__main__":
    main()
