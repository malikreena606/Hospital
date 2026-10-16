import base64
import os
import sqlite3
from datetime import date, datetime

import flet as ft

# ---------------------------------------------------------------
# إعدادات عامة
# ---------------------------------------------------------------
if os.environ.get("FLET_APP_STORAGE_DATA"):
    DB_PATH = os.path.join(os.environ["FLET_APP_STORAGE_DATA"], "kosti_hospital.db")
else:
    DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kosti_hospital.db")

ADMIN_PASSWORD = "1234"
MAX_RECEIPT_MB = 8  # أقصى حجم لصورة الإيصال

CLINICS = {
    "عيادة الباطنية": ("محمد أحمد", "باطنية", "الأحد - الخميس", "8 ص - 2 م"),
    "عيادة الجراحة": ("أمير محمد", "جراحة عامة", "السبت - الأربعاء", "8 ص - 2 م"),
    "عيادة الأطفال": ("سلمى خالد", "طب الأطفال", "الأحد - الخميس", "9 ص - 3 م"),
    "عيادة النساء والتوليد": ("هند عمر", "نساء وتوليد", "الأحد - الخميس", "9 ص - 3 م"),
}

# منتقي الملفات يُنشأ مرة واحدة فقط ويُضاف للصفحة في main
STATE = {"picker": None}


# ---------------------------------------------------------------
# قاعدة البيانات
# ---------------------------------------------------------------
def db(sql, params=(), fetch=None, commit=False):
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        cur.execute(sql, params)
        out = None
        if fetch == "one":
            out = cur.fetchone()
        elif fetch == "all":
            out = cur.fetchall()
        if commit:
            conn.commit()
        return out
    finally:
        conn.close()


def init_db():
    db("""
        CREATE TABLE IF NOT EXISTS patients (
            patient_id INTEGER PRIMARY KEY AUTOINCREMENT,
            national_id TEXT UNIQUE,
            phone_number TEXT,
            registered_at TEXT
        )
    """, commit=True)
    db("""
        CREATE TABLE IF NOT EXISTS appointments (
            appointment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_name TEXT,
            national_id TEXT,
            clinic_name TEXT,
            doctor_name TEXT,
            appointment_date TEXT,
            booked_at TEXT
        )
    """, commit=True)
    # ترقية قاعدة البيانات القديمة: إضافة أعمدة الدفع والإيصال إن لم تكن موجودة
    cols = [r[1] for r in db("PRAGMA table_info(appointments)", fetch="all")]
    if "payment_status" not in cols:
        db("ALTER TABLE appointments ADD COLUMN payment_status TEXT DEFAULT 'لم يتم الدفع'", commit=True)
    if "receipt" not in cols:
        db("ALTER TABLE appointments ADD COLUMN receipt BLOB", commit=True)


# ---------------------------------------------------------------
# أدوات مساعدة للواجهة
# ---------------------------------------------------------------
def show_snack(page, text, color=ft.Colors.BLUE_700):
    page.show_dialog(
        ft.SnackBar(
            content=ft.Text(text, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD),
            bgcolor=color,
            duration=3000,
        )
    )


def btn(text, on_click, bgcolor, color, height=45):
    return ft.Button(content=text, on_click=on_click, expand=True,
                     height=height, bgcolor=bgcolor, color=color)


def show_receipt(page, app_id):
    """يعرض صورة الإيصال المحفوظة للحجز في نافذة منبثقة."""
    row = db("SELECT receipt, patient_name FROM appointments WHERE appointment_id = ?",
             (app_id,), fetch="one")
    if not row or not row[0]:
        show_snack(page, "⚠️ لا توجد صورة إيصال لهذا الحجز", ft.Colors.RED_600)
        return
    b64 = base64.b64encode(row[0]).decode("ascii")
    dlg = ft.AlertDialog(
        title=ft.Text(f"إيصال الدفع - {row[1]}", size=16),
        content=ft.Container(
            content=ft.Image(src=b64, fit=ft.BoxFit.CONTAIN),
            width=320, height=420,
        ),
        actions=[ft.TextButton(content="إغلاق", on_click=lambda e: page.pop_dialog())],
    )
    page.show_dialog(dlg)


# ---------------------------------------------------------------
# 1) شاشة تسجيل الدخول
# ---------------------------------------------------------------
def show_login_screen(page):
    page.clean()
    name_field = ft.TextField(label="الاسم الكامل", text_align=ft.TextAlign.RIGHT, color=ft.Colors.BLACK)
    nat_field = ft.TextField(label="الرقم الوطني", keyboard_type=ft.KeyboardType.NUMBER,
                             max_length=11, color=ft.Colors.BLACK)
    phone_field = ft.TextField(label="رقم الهاتف", keyboard_type=ft.KeyboardType.PHONE,
                               max_length=10, color=ft.Colors.BLACK)

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
        if len(phone) != 10 or not phone.isdigit() or not phone.startswith("09"):
            show_snack(page, "⚠️ رقم الهاتف غير صحيح", ft.Colors.RED_600)
            return

        user = db("SELECT patient_id FROM patients WHERE national_id = ?", (nat,), fetch="one")
        if not user:
            db("INSERT INTO patients (national_id, phone_number, registered_at) VALUES (?, ?, ?)",
               (nat, phone, datetime.now().strftime("%Y-%m-%d %H:%M")), commit=True)
        else:
            db("UPDATE patients SET phone_number = ? WHERE national_id = ?", (phone, nat), commit=True)
        show_clinics_screen(page, name, nat)

    page.add(ft.Column([
        ft.Container(height=30),
        ft.Text("مستشفى كوستي التعليمي", size=22, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_900),
        ft.Text("نظام الحجز الالكتروني", size=14, color=ft.Colors.GREY_700),
        ft.Container(height=20),
        name_field, nat_field, phone_field,
        btn("تسجيل الدخول", handle_login, ft.Colors.BLUE_600, ft.Colors.WHITE, 50),
    ], spacing=12, horizontal_alignment=ft.CrossAxisAlignment.STRETCH))
    page.update()


# ---------------------------------------------------------------
# 2) شاشة العيادات
# ---------------------------------------------------------------
def show_clinics_screen(page, name, nat):
    page.clean()
    clinic_buttons = [
        btn(c, lambda ev, c=c: show_doctors_screen(page, c, name, nat),
            ft.Colors.BLUE_50, ft.Colors.BLUE_900)
        for c in CLINICS
    ]
    page.add(ft.Column([
        ft.Container(height=15),
        ft.Text(f"مرحباً: {name}", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.GREEN_700),
        ft.Text("اختر العيادة المطلوبة", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_900),
        *clinic_buttons,
        ft.Divider(),
        btn("📋 مواعيدي", lambda e: show_my_appointments_screen(page, nat, name),
            ft.Colors.ORANGE_100, ft.Colors.ORANGE_900),
        ft.Row([
            btn("👤 الإدارة", lambda e: show_admin_login_screen(page, name, nat),
                ft.Colors.PURPLE_100, ft.Colors.PURPLE_900, 40),
            btn("🚪 خروج", lambda e: show_login_screen(page),
                ft.Colors.RED_100, ft.Colors.RED_900, 40),
        ], spacing=10),
    ], spacing=12, horizontal_alignment=ft.CrossAxisAlignment.STRETCH))
    page.update()


# ---------------------------------------------------------------
# 3) شاشة الأطباء
# ---------------------------------------------------------------
def show_doctors_screen(page, clinic, name, nat):
    page.clean()
    doc_name, spec, days, hours = CLINICS[clinic]
    page.add(ft.Column([
        ft.Container(height=15),
        ft.Text(f"أطباء {clinic}", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_900),
        ft.Container(
            content=ft.Column([
                ft.Text(f"{doc_name} / {clinic}", size=14, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK),
                ft.Text(f"{spec} — {days} — {hours}", size=12, color=ft.Colors.BLACK),
                btn("📅 حجز موعد",
                    lambda ev: show_booking_screen(page, clinic, doc_name, spec, nat, name),
                    ft.Colors.GREEN_600, ft.Colors.WHITE, 42),
            ], spacing=8),
            padding=15, bgcolor=ft.Colors.BLUE_50, border_radius=12,
        ),
        btn("← العودة للعيادات", lambda e: show_clinics_screen(page, name, nat),
            ft.Colors.GREY_300, ft.Colors.BLACK, 40),
    ], spacing=15, horizontal_alignment=ft.CrossAxisAlignment.STRETCH))
    page.update()


# ---------------------------------------------------------------
# 4) شاشة الحجز + إرفاق الإيصال
# ---------------------------------------------------------------
def show_booking_screen(page, clinic, doctor, spec, nat, name):
    page.clean()
    name_field = ft.TextField(label="اسم المريض", value=name, border=ft.InputBorder.NONE,
                              filled=True, bgcolor=ft.Colors.GREY_100, color=ft.Colors.BLACK)
    date_field = ft.TextField(label="تاريخ الموعد (مثال: 2026-11-15)", border=ft.InputBorder.NONE,
                              filled=True, bgcolor=ft.Colors.GREY_100, color=ft.Colors.BLACK)

    receipt = {"data": None}  # بايتات الصورة المختارة
    attach_status = ft.Text("لم يتم إرفاق صورة", size=12, color=ft.Colors.RED_600)
    preview = ft.Image(src="", height=180, fit=ft.BoxFit.CONTAIN, visible=False)

    async def pick_receipt(e):
        files = await STATE["picker"].pick_files(
            allow_multiple=False,
            file_type=ft.FilePickerFileType.IMAGE,
        )
        if not files:
            return
        f = files[0]
        data = None
        try:
            if getattr(f, "path", None):
                with open(f.path, "rb") as fh:
                    data = fh.read()
            elif getattr(f, "bytes", None):
                data = f.bytes
        except Exception:
            data = None

        if not data:
            show_snack(page, "⚠️ تعذر قراءة الصورة، حاول مرة أخرى", ft.Colors.RED_600)
            return
        if len(data) > MAX_RECEIPT_MB * 1024 * 1024:
            show_snack(page, f"⚠️ حجم الصورة أكبر من {MAX_RECEIPT_MB} ميجا", ft.Colors.RED_600)
            return

        receipt["data"] = data
        attach_status.value = f"تم إرفاق الملف: {f.name} (تم الدفع) ✅"
        attach_status.color = ft.Colors.GREEN_700
        preview.src = base64.b64encode(data).decode("ascii")
        preview.visible = True
        page.update()

    def confirm_booking(ev):
        patient = (name_field.value or "").strip() or name
        date_val = (date_field.value or "").strip()
        try:
            d = datetime.strptime(date_val, "%Y-%m-%d").date()
        except ValueError:
            show_snack(page, "⚠️ صيغة التاريخ غير صحيحة (YYYY-MM-DD)", ft.Colors.RED_600)
            return
        if d < date.today():
            show_snack(page, "⚠️ لا يمكن الحجز في تاريخ سابق", ft.Colors.RED_600)
            return

        dup = db("SELECT 1 FROM appointments WHERE national_id=? AND clinic_name=? AND appointment_date=?",
                 (nat, clinic, date_val), fetch="one")
        if dup:
            show_snack(page, "⚠️ لديك حجز في هذه العيادة بنفس التاريخ", ft.Colors.RED_600)
            return

        paid = receipt["data"] is not None
        db("""INSERT INTO appointments
              (patient_name, national_id, clinic_name, doctor_name, appointment_date,
               booked_at, payment_status, receipt)
              VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
           (patient, nat, clinic, doctor, date_val,
            datetime.now().strftime("%Y-%m-%d %H:%M"),
            "تم الدفع" if paid else "لم يتم الدفع",
            receipt["data"]),
           commit=True)

        show_my_appointments_screen(page, nat, name)
        show_snack(page, "✅ تم تأكيد الحجز وحفظه بنجاح", ft.Colors.GREEN_600)

    page.add(ft.Column([
        ft.Container(height=10),
        ft.Text("حجز موعد جديد", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_900),
        ft.Text(f"{doctor} — {spec} — {clinic}", size=12, color=ft.Colors.GREY_800),
        ft.Text("بنكك: 9147234 | سعر تذكرة الموعد: 10,000 جنيه سوداني", size=11, color=ft.Colors.GREY_700),
        name_field,
        date_field,
        btn("📎 إرفاق صورة الإيصال", pick_receipt, ft.Colors.WHITE, ft.Colors.BLUE_900),
        attach_status,
        preview,
        btn("✅ تأكيد الحجز", confirm_booking, ft.Colors.GREEN_600, ft.Colors.WHITE, 50),
        btn("← العودة للأطباء", lambda e: show_doctors_screen(page, clinic, name, nat),
            ft.Colors.GREY_300, ft.Colors.BLACK, 40),
    ], spacing=12, horizontal_alignment=ft.CrossAxisAlignment.STRETCH))
    page.update()


# ---------------------------------------------------------------
# 5) شاشة مواعيدي
# ---------------------------------------------------------------
def show_my_appointments_screen(page, nat, name):
    page.clean()
    rows = db("""SELECT appointment_id, patient_name, clinic_name, doctor_name,
                        appointment_date, payment_status, receipt IS NOT NULL
                 FROM appointments WHERE national_id = ? ORDER BY appointment_id DESC""",
              (nat,), fetch="all")

    cards = []
    if not rows:
        cards.append(ft.Text("لا توجد مواعيد محجوزة", color=ft.Colors.GREY_600))
    for app_id, p_name, clinic, doctor, d, status, has_receipt in rows:
        paid = status == "تم الدفع"
        items = [
            ft.Text(f"رقم الحجز: #{app_id}", size=12, weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK),
            ft.Text(f"👤 {p_name}", weight=ft.FontWeight.BOLD, color=ft.Colors.BLACK),
            ft.Text(f"👨‍⚕️ {doctor} / {clinic}", size=12, color=ft.Colors.BLACK),
            ft.Text(f"📅 {d}", size=12, color=ft.Colors.BLACK),
            ft.Text(f"💳 {status}", size=12, weight=ft.FontWeight.BOLD,
                    color=ft.Colors.GREEN_700 if paid else ft.Colors.RED_600),
        ]
        if has_receipt:
            items.append(ft.TextButton(content="🧾 عرض الإيصال",
                                       on_click=lambda e, i=app_id: show_receipt(page, i)))
        cards.append(ft.Container(content=ft.Column(items, spacing=4),
                                  padding=12, bgcolor=ft.Colors.BLUE_50, border_radius=10))

    page.add(ft.Column([
        ft.Container(height=15),
        ft.Text("📋 مواعيدي", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_900),
        *cards,
        btn("← العودة للعيادات", lambda e: show_clinics_screen(page, name, nat),
            ft.Colors.GREY_300, ft.Colors.BLACK, 40),
    ], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.STRETCH))
    page.update()


# ---------------------------------------------------------------
# 6) لوحة الإدارة
# ---------------------------------------------------------------
def show_admin_login_screen(page, name, nat):
    page.clean()
    pass_field = ft.TextField(label="كلمة سر الإدارة", password=True, color=ft.Colors.BLACK)

    def check_pass(e):
        if (pass_field.value or "").strip() == ADMIN_PASSWORD:
            show_admin_reports(page, name, nat)
        else:
            show_snack(page, "⚠️ كلمة السر غير صحيحة", ft.Colors.RED_600)

    page.add(ft.Column([
        ft.Container(height=30),
        ft.Text("لوحة الإدارة", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.PURPLE_800),
        pass_field,
        btn("دخول", check_pass, ft.Colors.PURPLE_600, ft.Colors.WHITE),
        btn("← العودة", lambda e: show_clinics_screen(page, name, nat),
            ft.Colors.GREY_300, ft.Colors.BLACK, 40),
    ], spacing=15, horizontal_alignment=ft.CrossAxisAlignment.STRETCH))
    page.update()


def show_admin_reports(page, name, nat):
    page.clean()
    rows = db("""
        SELECT a.appointment_id, a.patient_name, a.appointment_date, a.clinic_name,
               p.phone_number, a.payment_status, a.receipt IS NOT NULL
        FROM appointments a
        LEFT JOIN patients p ON a.national_id = p.national_id
        ORDER BY a.appointment_id DESC
    """, fetch="all")

    def cancel_booking(app_id):
        db("DELETE FROM appointments WHERE appointment_id = ?", (app_id,), commit=True)
        show_admin_reports(page, name, nat)
        show_snack(page, "🗑️ تم إلغاء الحجز", ft.Colors.ORANGE_700)

    table_rows = []
    for app_id, p_name, d, clinic, phone, status, has_receipt in rows:
        paid = status == "تم الدفع"
        if has_receipt:
            receipt_cell = ft.IconButton(icon=ft.Icons.RECEIPT_LONG, icon_color=ft.Colors.BLUE_700,
                                         tooltip="عرض الإيصال",
                                         on_click=lambda e, i=app_id: show_receipt(page, i))
        else:
            receipt_cell = ft.Text("—", color=ft.Colors.GREY_600)
        table_rows.append(ft.DataRow(cells=[
            ft.DataCell(ft.Text(p_name or "", size=13, color=ft.Colors.BLACK)),
            ft.DataCell(ft.Text(d or "", size=13, color=ft.Colors.BLACK)),
            ft.DataCell(ft.Text(clinic or "", size=13, color=ft.Colors.BLACK)),
            ft.DataCell(ft.Text(phone or "", size=13, color=ft.Colors.BLACK)),
            ft.DataCell(ft.Text(status or "", size=13, weight=ft.FontWeight.BOLD,
                                color=ft.Colors.GREEN_700 if paid else ft.Colors.RED_600)),
            ft.DataCell(receipt_cell),
            ft.DataCell(ft.IconButton(icon=ft.Icons.DELETE, icon_color=ft.Colors.RED_600,
                                      tooltip="إلغاء الحجز",
                                      on_click=lambda e, i=app_id: cancel_booking(i))),
        ]))

    def head(t):
        return ft.DataColumn(ft.Text(t, color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD))

    table = ft.DataTable(
        columns=[head("الاسم"), head("الموعد"), head("العيادة"), head("رقم الهاتف"),
                 head("حالة الدفع"), head("الإيصال"), head("إلغاء")],
        rows=table_rows,
        heading_row_color=ft.Colors.PURPLE_600,
    )

    page.add(ft.Column([
        ft.Container(height=15),
        ft.Text(f"📊 تقارير الحجوزات ({len(rows)})", size=18,
                weight=ft.FontWeight.BOLD, color=ft.Colors.PURPLE_800),
        ft.Row([table], scroll=ft.ScrollMode.AUTO),
        ft.Container(height=10),
        btn("🚪 خروج من الإدارة", lambda e: show_clinics_screen(page, name, nat),
            ft.Colors.GREY_300, ft.Colors.BLACK, 40),
    ], spacing=15, horizontal_alignment=ft.CrossAxisAlignment.STRETCH))
    page.update()


# ---------------------------------------------------------------
def main(page: ft.Page):
    page.title = "مستشفى كوستي التعليمي"
    page.rtl = True
    page.scroll = ft.ScrollMode.AUTO
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.bgcolor = ft.Colors.WHITE

    init_db()

    # منتقي الملفات: يُنشأ مرة واحدة ويُضاف كخدمة للصفحة
    STATE["picker"] = ft.FilePicker()
    page.services.append(STATE["picker"])

    show_login_screen(page)


if __name__ == "__main__":
    ft.run(main)
