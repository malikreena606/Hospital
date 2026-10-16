import os
import sqlite3
from datetime import datetime
import flet as ft

# إعداد مسار قاعدة البيانات ليكون آمناً ومتوافقاً مع الهواتف الذكية
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
            payment_status TEXT,
            booked_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def show_snack(page, text, color=ft.colors.BLUE_700):
    snack = ft.SnackBar(
        content=ft.Text(text, color=ft.colors.WHITE, weight=ft.FontWeight.BOLD),
        bgcolor=color,
        duration=3000,
    )
    page.overlay.append(snack)
    snack.open = True
    page.update()

# 1. شاشة تسجيل الدخول
def show_login_screen(page):
    page.clean()
    name_field = ft.TextField(label="الاسم الكامل", expand=True, text_align=ft.TextAlign.RIGHT, color=ft.colors.BLACK)
    nat_field = ft.TextField(label="الرقم الوطني", expand=True, keyboard_type=ft.KeyboardType.NUMBER, max_length=11, color=ft.colors.BLACK)
    phone_field = ft.TextField(label="رقم الهاتف", expand=True, keyboard_type=ft.KeyboardType.PHONE, max_length=10, color=ft.colors.BLACK)

    def handle_login(ev):
        name = (name_field.value or "").strip()
        nat = (nat_field.value or "").strip()
        phone = (phone_field.value or "").strip()
        if not name or not nat or not phone:
            show_snack(page, "⚠️ أدخل جميع البيانات", ft.colors.RED_600)
            return
        if len(nat) != 11 or not nat.isdigit():
            show_snack(page, "⚠️ الرقم الوطني 11 رقماً", ft.colors.RED_600)
            return
        if len(phone) != 10 or not phone.startswith("09"):
            show_snack(page, "⚠️ رقم الهاتف غير صحيح", ft.colors.RED_600)
            return

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT patient_id FROM patients WHERE national_id = ?", (nat,))
        user = cursor.fetchone()
        if not user:
            cursor.execute("INSERT INTO patients (national_id, phone_number, registered_at) VALUES (?, ?, ?)",
                           (nat, phone, datetime.now().strftime("%Y-%m-%d %H:%M")))
            conn.commit()
        conn.close()
        show_clinics_screen(page, name, nat)

    page.add(
        ft.Column([
            ft.Container(height=30),
            ft.Text("مستشفى كوستي التعليمي", size=22, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_900),
            ft.Text("نظام الحجز الالكتروني", size=14, color=ft.colors.GREY_700),
            ft.Container(height=20),
            name_field,
            nat_field,
            phone_field,
            ft.ElevatedButton(text="تسجيل الدخول", on_click=handle_login, expand=True, height=50, bgcolor=ft.colors.BLUE_600, color=ft.colors.WHITE),
        ], spacing=12, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    )
    page.update()

# 2. شاشة عرض العيادات
def show_clinics_screen(page, name, nat):
    page.clean()
    clinics = ["عيادة الباطنية", "عيادة الجراحة", "عيادة الأطفال", "عيادة النساء والتوليد"]
    buttons = []
    for c in clinics:
        def make_handler(clinic_name):
            return lambda ev: show_doctors_screen(page, clinic_name, name, nat)
        buttons.append(ft.ElevatedButton(text=c, on_click=make_handler(c), expand=True, height=45, bgcolor=ft.colors.BLUE_50, color=ft.colors.BLUE_900))

    page.add(
        ft.Column([
            ft.Container(height=15),
            ft.Text(f"مرحباً: {name}", size=14, weight=ft.FontWeight.BOLD, color=ft.colors.GREEN_700),
            ft.Text("اختر العيادة المطلوبة", size=20, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_900),
            *buttons,
            ft.Divider(),
            ft.ElevatedButton(text="📋 مواعيدي", on_click=lambda e: show_my_appointments_screen(page, nat, name), expand=True, height=45, bgcolor=ft.colors.ORANGE_100, color=ft.colors.ORANGE_900),
            ft.Row([
                ft.ElevatedButton(text="👤 الإدارة", on_click=lambda e: show_admin_login_screen(page, name, nat), expand=True, height=40, bgcolor=ft.colors.PURPLE_100, color=ft.colors.PURPLE_900),
                ft.ElevatedButton(text="🚪 خروج", on_click=lambda e: show_login_screen(page), expand=True, height=40, bgcolor=ft.colors.RED_100, color=ft.colors.RED_900),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        ], spacing=12, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
    )
    page.update()

# شاشة دخول لوحة الإدارة
def show_admin_login_screen(page, name, nat):
    page.clean()
    pass_field = ft.TextField(label="كلمة سر الإدارة", password=True, can_reveal_password=False, expand=True, color=ft.colors.BLACK)

    def check_pass(e):
        if (pass_field.value or "").strip() == "1234":
            show_admin_reports(page, name, nat)
        else:
            show_snack(page, "⚠️ كلمة السر غير صحيحة", ft.colors.RED_600)

    page.add(
        ft.Column([
            ft.Container(height=30),
            ft.Text("لوحة الإدارة", size=20, weight=ft.FontWeight.BOLD, color=ft.colors.PURPLE_800),
            pass_field,
            ft.ElevatedButton(text="دخول", on_click=check_pass, expand=True, height=45, bgcolor=ft.colors.PURPLE_600, color=ft.colors.WHITE),
            ft.ElevatedButton(text="← العودة", on_click=lambda e: show_clinics_screen(page, name, nat), expand=True, height=40, bgcolor=ft.colors.GREY_300, color=ft.colors.BLACK),
        ], spacing=15, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
    )
    page.update()

# 3. شاشة عرض الأطباء
def show_doctors_screen(page, clinic, name, nat):
    page.clean()
    doctors_data = {
        "عيادة الباطنية": ("محمد أحمد", "باطنية", "الأحد - الخميس", "8 ص - 2 م"),
        "عيادة الجراحة": ("أمير محمد", "جراحة عامة", "السبت - الأربعاء", "8 ص - 2 م"),
        "عيادة الأطفال": ("سلمى خالد", "طب الأطفال", "الأحد - الخميس", "9 ص - 3 م"),
        "عيادة النساء والتوليد": ("هند عمر", "نساء وتوليد", "الأحد - الخميس", "9 ص - 3 م")
    }
    doc_name, spec, days, hours = doctors_data.get(clinic, ("", "", "", ""))

    page.add(
        ft.Column([
            ft.Container(height=15),
            ft.Text(f"أطباء {clinic}", size=18, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_900),
            ft.Container(
                content=ft.Column([
                    ft.Text(f"{doc_name} / {clinic}", size=14, weight=ft.FontWeight.BOLD),
                    ft.Text(f"{spec} — {days} — {hours}", size=12),
                    ft.ElevatedButton(text="📅 حجز موعد", on_click=lambda ev: show_booking_screen(page, clinic, doc_name, spec, nat, name), expand=True, height=42, bgcolor=ft.colors.GREEN_600, color=ft.colors.WHITE),
                ], spacing=8),
                padding=15, bgcolor=ft.colors.BLUE_50, border_radius=12
            ),
            ft.ElevatedButton(text="← العودة للعيادات", on_click=lambda e: show_clinics_screen(page, name, nat), expand=True, height=40, bgcolor=ft.colors.GREY_300, color=ft.colors.BLACK),
        ], spacing=15, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
    )
    page.update()

# 4. شاشة تأكيد وحجز الموعد
def show_booking_screen(page, clinic, doctor, spec, nat, name):
    page.clean()
    name_field = ft.TextField(label="اسم المريض", value=name, expand=True, border=ft.InputBorder.NONE, filled=True, bgcolor=ft.colors.GREY_100, color=ft.colors.BLACK)
    date_field = ft.TextField(label="تاريخ الموعد (مثال: 2026-06-15)", expand=True, border=ft.InputBorder.NONE, filled=True, bgcolor=ft.colors.GREY_100, color=ft.colors.BLACK)

    receipt_attached = {"value": False}
    attach_status = ft.Text("لم يتم إرفاق صورة", size=12, color=ft.colors.RED_600)

    def on_file_picked(e: ft.FilePickerResultEvent):
        if e.files:
            receipt_attached["value"] = True
            attach_status.value = f"تم إرفاق الملف: {e.files[0].name} (تم الدفع) ✅"
            attach_status.color = ft.colors.GREEN_700
            page.update()

    file_picker = ft.FilePicker(on_result=on_file_picked)
    page.overlay.append(file_picker)
    page.update()

    attach_button = ft.ElevatedButton(
        text="إرفاق صورة الإيصال",
        bgcolor=ft.colors.WHITE,
        color=ft.colors.BLUE_900,
        height=45,
        expand=True,
        on_click=lambda _: file_picker.pick_files(allow_multiple=False, file_type=ft.FilePickerFileType.IMAGE)
    )

    def confirm_booking(ev):
        date_val = (date_field.value or "").strip()
        if not date_val:
            show_snack(page, "⚠️ أدخل تاريخ الموعد", ft.colors.RED_600)
            return

        payment_str = "تم الدفع" if receipt_attached["value"] else "لم يتم إرفاق صورة"

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO appointments (patient_name, national_id, clinic_name, doctor_name, appointment_date, payment_status, booked_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name, nat, clinic, doctor, date_val, payment_str, datetime.now().strftime("%Y-%m-%d %H:%M")))
        conn.commit()
        conn.close()

        show_snack(page, "✅ تم تأكيد الحجز وحفظه بنجاح", ft.colors.GREEN_600)
        show_my_appointments_screen(page, nat, name)

    page.add(
        ft.Column([
            ft.Container(height=10),
            ft.Text("حجز موعد جديد", size=20, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_900),
            ft.Text("بنكك: 9147234 | سعر تذكرة الموعد: 10,000 جنيه سوداني", size=11, color=ft.colors.GREY_700),
            name_field,
            date_field,
            attach_button,
            attach_status,
            ft.ElevatedButton(text="✅ تأكيد الحجز", on_click=confirm_booking, expand=True, height=50, bgcolor=ft.colors.GREEN_600, color=ft.colors.WHITE),
            ft.ElevatedButton(text="← العودة للأطباء", on_click=lambda e: show_doctors_screen(page, clinic, name, nat), expand=True, height=40, bgcolor=ft.colors.GREY_300, color=ft.colors.BLACK),
        ], spacing=12, horizontal_alignment=ft.CrossAxisAlignment.STRETCH)
    )
    page.update()

# 5. شاشة مواعيدي
def show_my_appointments_screen(page, nat, name):
    page.clean()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT appointment_id, patient_name, clinic_name, doctor_name, appointment_date, payment_status
        FROM appointments WHERE national_id = ? ORDER BY appointment_id DESC
    """, (nat,))
    rows = cursor.fetchall()
    conn.close()

    cards = []
    if not rows:
        cards.append(ft.Text("لا توجد مواعيد محجوزة", color=ft.colors.GREY_600))
    else:
        for app_id, p_name, clinic, doctor, date, p_status in rows:
            cards.append(
                ft.Container(
                    content=ft.Column([
                        ft.Text(f"رقم الحجز: #{app_id}", size=12, weight=ft.FontWeight.BOLD, color=ft.colors.BLACK),
                        ft.Text(f"👤 {p_name}", weight=ft.FontWeight.BOLD, color=ft.colors.BLACK),
                        ft.Text(f"👨‍⚕️ {doctor} / {clinic}", size=12, color=ft.colors.BLACK),
                        ft.Text(f"📅 {date}", size=12, color=ft.colors.BLACK),
                        ft.Text(f"💳 الحالة: {p_status}", size=12, color=ft.colors.GREEN_700 if "تم الدفع" in p_status else ft.colors.RED_600, weight=ft.FontWeight.BOLD),
                    ], spacing=4),
                    padding=12, bgcolor=ft.colors.BLUE_50, border_radius=10
                )
            )

    page.add(
        ft.Column([
            ft.Container(height=15),
            ft.Text("📋 مواعيدي", size=20, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_900),
            *cards,
            ft.ElevatedButton(text="← العودة للعيادات", on_click=lambda e: show_clinics_screen(page, name, nat), expand=True, height=40, bgcolor=ft.colors.GREY_300, color=ft.colors.BLACK),
        ], spacing=10, expand=True, horizontal_alignment=ft.CrossAxisAlignment.STRETCH, scroll=ft.ScrollMode.AUTO)
    )
    page.update()

# 6. شاشة تقارير الحجوزات الإدارية
def show_admin_reports(page, name, nat):
    page.clean()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT patient_name, clinic_name, appointment_date, payment_status
        FROM appointments ORDER BY appointment_id DESC
    """)
    rows = cursor.fetchall()
    conn.close()

    table_rows = []
    for p_name, clinic, date, p_status in rows:
        table_rows.append(
            ft.DataRow(cells=[
                ft.DataCell(ft.Text(p_name or "", size=13, color=ft.colors.BLACK)),
                ft.DataCell(ft.Text(clinic or "", size=13, color=ft.colors.BLACK)),
                ft.DataCell(ft.Text(date or "", size=13, color=ft.colors.BLACK)),
                ft.DataCell(ft.Text(p_status or "", size=13, color=ft.colors.GREEN_700 if "تم الدفع" in p_status else ft.colors.RED_600, weight=ft.FontWeight.BOLD)),
            ])
        )

    table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("اسم المريض", color=ft.colors.WHITE, weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("عيادة", color=ft.colors.WHITE, weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("الموعد", color=ft.colors.WHITE, weight=ft.FontWeight.BOLD)),
            ft.DataColumn(ft.Text("حالة الدفع", color=ft.colors.WHITE, weight=ft.FontWeight.BOLD)),
        ],
        rows=table_rows,
        heading_row_color=ft.colors.PURPLE_600,
    )

    page.add(
        ft.Column([
            ft.Container(height=15),
            ft.Text("📊 تقارير الحجوزات الإدارية", size=18, weight=ft.FontWeight.BOLD, color=ft.colors.PURPLE_800),
            table,
            ft.Container(height=10),
            ft.ElevatedButton(text="← العودة للعيادات", on_click=lambda e: show_clinics_screen(page, name, nat), expand=True, height=40, bgcolor=ft.colors.GREY_300, color=ft.colors.BLACK),
        ], spacing=15, horizontal_alignment=ft.CrossAxisAlignment.CENTER, scroll=ft.ScrollMode.AUTO)
    )
    page.update()

def main(page: ft.Page):
    page.title = "مستشفى كوستي التعليمي"
    page.rtl = True
    page.scroll = ft.ScrollMode.AUTO
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.bgcolor = ft.colors.WHITE

    init_db()
    show_login_screen(page)

if __name__ == "__main__":
    ft.app(target=main)
