import flet as ft
import sqlite3
import os
from datetime import datetime

if os.environ.get("FLET_APP_STORAGE_DATA"):
    DB_PATH = os.path.join(os.environ["FLET_APP_STORAGE_DATA"], "kosti_hospital.db")
else:
    DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kosti_hospital.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            patient_id INTEGER PRIMARY KEY AUTOINCREMENT,
            national_id TEXT UNIQUE,
            phone_number TEXT,
            registered_at TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            appointment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_name TEXT,
            national_id TEXT,
            clinic_name TEXT,
            doctor_name TEXT,
            appointment_date TEXT,
            receipt_image TEXT,
            booked_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def show_snack(page, text, color=ft.Colors.BLUE_700):
    snack = ft.SnackBar(
        content=ft.Text(text, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
        bgcolor=color,
        duration=3000
    )
    page.show_dialog(snack)
    page.update()

def show_login_screen(page):
    page.clean()
    name_field = ft.TextField(label="الاسم الكامل", expand=True, text_align=ft.TextAlign.RIGHT)
    nat_field = ft.TextField(label="الرقم الوطني", expand=True, keyboard_type=ft.KeyboardType.NUMBER, max_length=11)
    phone_field = ft.TextField(label="رقم الهاتف", expand=True, keyboard_type=ft.KeyboardType.PHONE, max_length=10)
    
    def handle_login(ev):
        name = (name_field.value or "").strip()
        nat = (nat_field.value or "").strip()
        phone = (phone_field.value or "").strip()
        if not name or not nat or not phone:
            show_snack(page, "⚠️ أدخل جميع البيانات", ft.Colors.RED_600)
            return
        if len(nat) != 11 or not nat.isdigit():
            show_snack(page, "⚠️ الرقم الوطني 11 رقماً", ft.Colors.RED_600)
            return
        if len(phone) != 10 or not phone.startswith("09"):
            show_snack(page, "⚠️ رقم الهاتف غير صحيح", ft.Colors.RED_600)
            return
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT patient_id FROM patients WHERE national_id = ?", (nat,))
        user = cursor.fetchone()
        if not user:
            cursor.execute("""INSERT INTO patients 
                (national_id, phone_number, registered_at) VALUES (?, ?, ?)""",
                (nat, phone, datetime.now().strftime("%Y-%m-%d %H:%M")))
            conn.commit()
        conn.close()
        show_clinics_screen(page, name, nat)

    page.add(ft.Column([
        ft.Text("مستشفى كوستي التعليمي", size=22, weight=ft.FontWeight.BOLD),
        name_field, nat_field, phone_field,
        ft.Button(content="تسجيل الدخول", on_click=handle_login,
                  expand=True, height=50, bgcolor=ft.Colors.BLUE_600, color=ft.Colors.WHITE)
    ], spacing=12))
    page.update()

def show_clinics_screen(page, name, nat):
    page.clean()
    clinics = ["عيادة الباطنية", "عيادة الجراحة", "عيادة الأطفال", "عيادة النساء والتوليد"]
    buttons = []
    for c in clinics:
        def make_handler(clinic_name):
            def handler(ev):
                show_doctors_screen(page, clinic_name, name, nat)
            return handler
        buttons.append(ft.Button(
            content=c, on_click=make_handler(c),
            expand=True, height=45,
            bgcolor=ft.Colors.BLUE_50, color=ft.Colors.BLUE_900
        ))
    
    page.add(ft.Column([
        ft.Text(f"مرحباً: {name}", size=14, color=ft.Colors.GREEN_700),
        ft.Text("اختر العيادة المطلوبة", size=20, weight=ft.FontWeight.BOLD),
        *buttons,
        ft.Row([
            ft.Button(content="📋 مواعيدي", on_click=lambda e: show_my_appointments_screen(page, nat), expand=True, bgcolor=ft.Colors.ORANGE_300),
            ft.Button(content="🚪 خروج", on_click=lambda e: show_login_screen(page), expand=True, bgcolor=ft.Colors.RED_300),
        ])
    ], spacing=10, expand=True))
    page.update()

def show_doctors_screen(page, clinic, name, nat):
    page.clean()
    doctors_data = {
        "عيادة الباطنية": ("محمد أحمد", "باطنية", "الأحد - الخميس", "8 ص - 2 م"),
        "عيادة الجراحة": ("أمير محمد", "جراحة عامة", "السبت - الأربعاء", "8 ص - 2 م"),
        "عيادة الأطفال": ("سلمى خالد", "طب الأطفال", "الأحد - الخميس", "9 ص - 3 م"),
        "عيادة النساء والتوليد": ("هند عمر", "نساء وتوليد", "الأحد - الخميس", "9 ص - 3 م"),
    }
    doc_name, spec, days, hours = doctors_data.get(clinic, ("", "", "", ""))
    
    def book(ev):
        show_booking_screen(page, clinic, doc_name, spec, nat, name)

    page.add(ft.Column([
        ft.Text(f"أطباء {clinic}", size=18, weight=ft.FontWeight.BOLD),
        ft.Container(
            content=ft.Column([
                ft.Text(f"{doc_name} / {clinic}", size=14, weight=ft.FontWeight.BOLD),
                ft.Text(f"{spec} — {days} — {hours}", size=12),
                ft.Button(content="📅 حجز موعد", on_click=book,
                          expand=True, height=42, bgcolor=ft.Colors.GREEN_600, color=ft.Colors.WHITE)
            ], spacing=8),
            padding=15, bgcolor=ft.Colors.BLUE_50, border_radius=12
        ),
        ft.TextButton(content="← العودة للعيادات", on_click=lambda e: show_clinics_screen(page, name, nat))
    ], spacing=15))
    page.update()

def show_booking_screen(page, clinic, doctor, spec, nat, name):
    page.clean()
    name_field = ft.TextField(label="اسم المريض", value=name, expand=True)
    date_field = ft.TextField(label="تاريخ الموعد (مثال: 2026-06-15)", expand=True)
    image_field = ft.TextField(label="اسم أو وصف صورة التحويل (اختياري)", expand=True)
    
    def confirm_booking(ev):
        date_val = (date_field.value or "").strip()
        if not date_val:
            show_snack(page, "⚠️ أدخل التاريخ", ft.Colors.RED_600)
            return
        img_val = (image_field.value or "").strip()
        
        conn = sqlite3.connect(DB_PATH)
        conn.execute("""INSERT INTO appointments 
            (patient_name, national_id, clinic_name, doctor_name,
             appointment_date, receipt_image, booked_at) VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (name, nat, clinic, doctor, date_val, img_val,
             datetime.now().strftime("%Y-%m-%d %H:%M")))
        conn.commit()
        conn.close()
        
        show_snack(page, "✅ تم تأكيد الحجز بنجاح", ft.Colors.GREEN_600)
        show_my_appointments_screen(page, nat)

    page.add(ft.Column([
        ft.Text("حجز موعد جديد", size=20, weight=ft.FontWeight.BOLD),
        ft.Container(
            content=ft.Column([
                ft.Text(f"طبيب: {doctor} / {clinic}", weight=ft.FontWeight.BOLD),
                ft.Text("رقم الحساب: 9147234 — سعر التذكرة: 10,000 جنيه سوداني", size=12, color=ft.Colors.BLUE_900)
            ]),
            padding=10, bgcolor=ft.Colors.BLUE_50, border_radius=8
        ),
        name_field,
        date_field,
        image_field,
        ft.Button(content="✅ تأكيد الحجز", on_click=confirm_booking,
                  expand=True, height=50, bgcolor=ft.Colors.GREEN_600, color=ft.Colors.WHITE),
        ft.TextButton(content="← العودة للأطباء", on_click=lambda e: show_clinics_screen(page, name, nat))
    ], spacing=15, scroll=ft.ScrollMode.AUTO))
    page.update()

def show_my_appointments_screen(page, nat):
    page.clean()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""SELECT appointment_id, patient_name, clinic_name, doctor_name, appointment_date, receipt_image
        FROM appointments WHERE national_id = ? ORDER BY appointment_id DESC""", (nat,))
    rows = cursor.fetchall()
    conn.close()
    
    cards = []
    if not rows:
        cards.append(ft.Text("لا توجد مواعيد محجوزة", color=ft.Colors.GREY_600))
    else:
        for app_id, name, clinic, doctor, date, img in rows:
            cards.append(ft.Container(
                content=ft.Column([
                    ft.Text(f"رقم الحجز: #{app_id}", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_700),
                    ft.Text(f"👤 {name}", weight=ft.FontWeight.BOLD),
                    ft.Text(f"👨‍⚕️ {doctor} / {clinic}", size=12),
                    ft.Text(f"📅 {date}", size=12),
                    ft.Text(f"📎 الصورة المرفقة: {img if img else 'لا توجد'}", size=11, color=ft.Colors.GREY_700)
                ], spacing=4),
                padding=12, bgcolor=ft.Colors.BLUE_50, border_radius=10
            ))
            
    page.add(ft.Column([
        ft.Text("📋 مواعيدي", size=20, weight=ft.FontWeight.BOLD),
        *cards,
        ft.TextButton(content="← العودة للعيادات", on_click=lambda e: show_clinics_screen(page, "", nat))
    ], spacing=10, expand=True, scroll=ft.ScrollMode.AUTO))
    page.update()

def show_admin_dashboard(page):
    page.clean()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.patient_name, a.appointment_date,
               a.clinic_name, p.phone_number, a.receipt_image
        FROM appointments a
        LEFT JOIN patients p ON a.national_id = p.national_id
        ORDER BY a.appointment_id DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    
    table_rows = []
    for name, date, clinic, phone, img in rows:
        table_rows.append(ft.DataRow(cells=[
            ft.DataCell(ft.Text(name or "", size=14)),
            ft.DataCell(ft.Text(date or "", size=14)),
            ft.DataCell(ft.Text(clinic or "", size=14)),
            ft.DataCell(ft.Text(phone or "", size=14)),
            ft.DataCell(ft.Text(img if img else "فارغ", size=12, color=ft.Colors.BLUE_800)),
        ]))
        
    table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("الاسم", color=ft.Colors.WHITE)),
            ft.DataColumn(ft.Text("الموعد", color=ft.Colors.WHITE)),
            ft.DataColumn(ft.Text("العيادة", color=ft.Colors.WHITE)),
            ft.DataColumn(ft.Text("رقم الهاتف", color=ft.Colors.WHITE)),
            ft.DataColumn(ft.Text("صورة الإيصال", color=ft.Colors.WHITE)),
        ],
        rows=table_rows,
        heading_row_color=ft.Colors.PURPLE_600,
    )
    
    page.add(ft.Column([
        ft.Text("تقارير الحجوزات مع إيصالات الدفع", size=20, weight=ft.FontWeight.BOLD),
        table,
        ft.TextButton(content="← تسجيل الخروج من الإدارة", on_click=lambda e: show_login_screen(page))
    ], expand, scroll=ft.ScrollMode.AUTO))
    page.update()

def main(page: ft.Page):
    page.title = "مستشفى كوستي التعليمي"
    page.rtl = True
    page.scroll = ft.ScrollMode.AUTO
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    init_db()
    show_login_screen(page)

if __name__ == "__main__":
    ft.run(main)

```
