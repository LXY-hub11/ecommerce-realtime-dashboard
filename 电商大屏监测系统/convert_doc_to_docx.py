# -*- coding: utf-8 -*-
"""Convert .doc to .docx using Word COM automation"""
import os
import sys

TEMPLATE_DOC = r"D:\项目\1\电商大屏监测系统\课程设计报告模板-大数据综合实训-0.doc"
TEMPLATE_DOCX = r"D:\项目\1\电商大屏监测系统\课程设计报告模板-大数据综合实训-0.docx"

print(f"Converting: {TEMPLATE_DOC}")
print(f"       To: {TEMPLATE_DOCX}")

if os.path.exists(TEMPLATE_DOCX):
    print("Target .docx already exists, skipping conversion.")
    sys.exit(0)

import win32com.client

word = win32com.client.Dispatch("Word.Application")
word.Visible = False
word.DisplayAlerts = False

try:
    doc = word.Documents.Open(TEMPLATE_DOC)
    # Save as .docx (Format: 16 = wdFormatXMLDocument)
    doc.SaveAs(TEMPLATE_DOCX, FileFormat=16)
    doc.Close()
    print("Conversion successful!")
finally:
    word.Quit()

print("Done.")
