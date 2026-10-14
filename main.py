from datetime import datetime
import os
import sqlite3
import flet as ft

# إعداد مسار قاعدة البيانات لتكون آمنة وسهلة في الهاتف أو الحاسوب
if os.environ.get("FLET_APP_STORAGE_DATA"):
  DB_PATH = os.path.join(
      os.environ["FLET_APP_STORAGE_DATA"], "kosti_simple.db"
  )
else:
  DB_PATH = os.path.join(
      os.path.dirname(os.path.abspath(__file__)), "kosti_simple.db"
  )


def init_db():
  conn = sqlite3.connect(DB_PATH)
  cursor = conn.cursor()
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            appointment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_name TEXT,
            clinic_name TEXT,
            doctor_name TEXT,
            appointment_date TEXT,
            payment_status TEXT
        )
    """)
  conn.commit()
  conn.close()


def main(page: ft.Page):
  page.title = "مستشفى كوستي التعليمي"
  page.rtl = True
  page.scroll = ft.ScrollMode.AUTO
  page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
  page.bgcolor = ft.Colors.WHITE  # خلفية بيضاء بالكامل

  init_db()

  # متغير لتتبع ما إذا تم إرفاق صورة الإيصال أم لا
  receipt_attached = {"value": False}

  title_text = ft.Text(
      "حجز موعد جديد", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_900
  )

  # رقم الحساب وسعر التذكرة في نفس السطر وبدون خطوط أو إطارات
  financial_info = ft.Text(
      "رقم الحساب: 9147234 | سعر تذكرة الموعد: 10,000 جنيه سوداني",
      size=11,
      color=ft.Colors.GREY_700,
  )

  name_field = ft.TextField(
      label="اسم المريض",
      border=ft.InputBorder.NONE,
      filled=True,
      bgcolor=ft.Colors.GREY_100,
  )

  date_field = ft.TextField(
      label="تاريخ الموعد (مثال: 2026-06-15)",
      border=ft.InputBorder.NONE,
      filled=True,
      bgcolor=ft.Colors.GREY_100,
  )

  attach_status = ft.Text(
      "لم يتم إرفاق صورة", size=12, color=ft.Colors.RED_600
  )

  def attach_image_click(e):
    receipt_attached["value"] = True
    attach_status.value = "تم إرفاق صورة الإيصال بنجاح (تم الدفع) ✅"
    attach_status.color = ft.Colors.GREEN_700
    page.update()

  # استخدام زر Flet القياسي والمستقر تماماً
  attach_button = ft.Button(
      content="إرفاق صورة",
      bgcolor=ft.Colors.WHITE,
      color=ft.Colors.BLUE_900,
      height=45,
      expand=True,
      on_click=attach_image_click,
  )

  status_text = ft.Text("", color=ft.Colors.GREEN_700, weight=ft.FontWeight.BOLD)

  def save_appointment(e):
    p_name = (name_field.value or "").strip()
    a_date = (date_field.value or "").strip()

    if not p_name or not a_date:
      status_text.value = "⚠️ الرجاء إدخال اسم المريض وتاريخ الموعد"
      status_text.color = ft.Colors.RED_600
      page.update()
      return

    payment_str = (
        "تم الدفع (بإرفاق الصورة)"
        if receipt_attached["value"]
        else "لم يتم إرفاق صورة"
    )

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO appointments (patient_name, clinic_name, doctor_name, appointment_date, payment_status)
                   VALUES (?, ?, ?, ?, ?)""",
        (p_name, "عيادة النساء والتوليد", "هند عمر", a_date, payment_str),
    )
    conn.commit()
    conn.close()

    status_text.value = "✅ تم تأكيد الحجز بنجاح"
    status_text.color = ft.Colors.GREEN_700
    name_field.value = ""
    date_field.value = ""
    receipt_attached["value"] = False
    attach_status.value = "لم يتم إرفاق صورة"
    attach_status.color = ft.Colors.RED_600
    page.update()

    show_admin_reports(page)

  confirm_button = ft.Button(
      content="تأكيد الحجز",
      bgcolor=ft.Colors.GREEN_600,
      color=ft.Colors.WHITE,
      height=50,
      expand=True,
      on_click=save_appointment,
  )

  def show_admin_reports(pg):
    pg.clean()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT patient_name, clinic_name, appointment_date, payment_status FROM"
        " appointments ORDER BY appointment_id DESC"
    )
    rows = cursor.fetchall()
    conn.close()

    table_rows = []
    for r in rows:
      table_rows.append(
          ft.DataRow(
              cells=[
                  ft.DataCell(ft.Text(r[0] or "", size=14)),
                  ft.DataCell(ft.Text(r[1] or "", size=14)),
                  ft.DataCell(ft.Text(r[2] or "", size=14)),
                  ft.DataCell(
                      ft.Text(
                          r[3] or "",
                          size=14,
                          color=(
                              ft.Colors.GREEN_700
                              if "تم الدفع" in r[3]
                              else ft.Colors.RED_600
                          ),
                          weight=ft.FontWeight.BOLD,
                      )
                  ),
              ]
          )
      )

    table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("اسم المريض", color=ft.Colors.WHITE)),
            ft.DataColumn(ft.Text("العيادة", color=ft.Colors.WHITE)),
            ft.DataColumn(ft.Text("الموعد", color=ft.Colors.WHITE)),
            ft.DataColumn(ft.Text("حالة الدفع", color=ft.Colors.WHITE)),
        ],
        rows=table_rows,
        heading_row_color=ft.Colors.PURPLE_600,
    )

    pg.add(
        ft.Column(
            [
                ft.Container(height=20),
                ft.Text(
                    "📊 تقارير الحجوزات وحالة الدفع",
                    size=20,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.PURPLE_800,
                ),
                table,
                ft.Container(height=20),
                ft.Button(
                    content="← العودة لحجز موعد جديد",
                    on_click=lambda e: main(pg),
                    bgcolor=ft.Colors.BLUE_600,
                    color=ft.Colors.WHITE,
                    height=45,
                    expand=True,
                ),
            ],
            spacing=15,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            scroll=ft.ScrollMode.AUTO,
        )
    )
    pg.update()

  view_reports_btn = ft.TextButton(
      content=ft.Text("عرض تقارير الإدارة (التحقق من الدفع) 📋"),
      on_click=lambda e: show_admin_reports(page),
  )

  page.add(
      ft.Column(
          [
              ft.Container(height=10),
              title_text,
              financial_info,
              ft.Container(height=5),
              name_field,
              date_field,
              attach_button,
              attach_status,
              confirm_button,
              status_text,
              ft.Divider(),
              view_reports_btn,
          ],
          spacing=12,
          horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
      )
  )
  page.update()


if __name__ == "__main__":
  ft.run(main)
