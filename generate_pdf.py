from markdown_pdf import MarkdownPdf, Section

# Read the markdown report
with open(r"C:\Users\Youssef\.gemini\antigravity\brain\7eafd4db-227c-42df-90a0-052c7c947c31\system_refactor_report.md", "r", encoding="utf-8") as f:
    markdown_content = f.read()

# Create a PDF
pdf = MarkdownPdf()
pdf.add_section(Section(markdown_content))
pdf.save(r"C:\Users\Youssef\OneDrive\Desktop\DP project\School-Information-System\system_refactor_report.pdf")
print("PDF created successfully!")
