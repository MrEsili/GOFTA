from pathlib import Path
from xml.sax.saxutils import escape

import arabic_reshaper
from bidi.algorithm import get_display
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "GOFTA_V3_GUIDE_FA.pdf"
FONT = Path(r"C:\Windows\Fonts\tahoma.ttf")
FONT_BOLD = Path(r"C:\Windows\Fonts\tahomabd.ttf")

pdfmetrics.registerFont(TTFont("Tahoma", str(FONT)))
pdfmetrics.registerFont(TTFont("Tahoma-Bold", str(FONT_BOLD)))
pdfmetrics.registerFontFamily(
    "Tahoma", normal="Tahoma", bold="Tahoma-Bold", italic="Tahoma", boldItalic="Tahoma-Bold"
)

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(
    name="FaTitle", fontName="Tahoma-Bold", fontSize=27, leading=42,
    alignment=TA_CENTER, textColor=colors.HexColor("#2459a6"), spaceAfter=12,
))
styles.add(ParagraphStyle(
    name="FaSubtitle", fontName="Tahoma", fontSize=14, leading=25,
    alignment=TA_CENTER, textColor=colors.HexColor("#536277"), spaceAfter=12,
))
styles.add(ParagraphStyle(
    name="FaH1", fontName="Tahoma-Bold", fontSize=17, leading=29,
    alignment=TA_RIGHT, textColor=colors.HexColor("#2459a6"),
    spaceBefore=8, spaceAfter=10, keepWithNext=True,
))
styles.add(ParagraphStyle(
    name="FaH2", fontName="Tahoma-Bold", fontSize=12, leading=22,
    alignment=TA_RIGHT, textColor=colors.HexColor("#253349"),
    spaceBefore=7, spaceAfter=4, keepWithNext=True,
))
styles.add(ParagraphStyle(
    name="FaBody", fontName="Tahoma", fontSize=9.4, leading=18,
    alignment=TA_RIGHT, textColor=colors.HexColor("#273344"),
    spaceAfter=6, wordWrap="RTL",
))
styles.add(ParagraphStyle(
    name="FaSmall", fontName="Tahoma", fontSize=8, leading=15,
    alignment=TA_RIGHT, textColor=colors.HexColor("#526176"), spaceAfter=4,
))
styles.add(ParagraphStyle(
    name="FaCode", fontName="Courier", fontSize=8.5, leading=13,
    alignment=TA_RIGHT, textColor=colors.HexColor("#f4f7fb"),
    backColor=colors.HexColor("#202b3a"), borderPadding=8, spaceBefore=3, spaceAfter=9,
))
styles.add(ParagraphStyle(
    name="FaCallout", fontName="Tahoma-Bold", fontSize=9.2, leading=18,
    alignment=TA_RIGHT, textColor=colors.HexColor("#704d0b"),
    backColor=colors.HexColor("#fff4d6"), borderPadding=9, spaceBefore=4, spaceAfter=9,
))


def fa(text, style="FaBody"):
    shaped = get_display(arabic_reshaper.reshape(text))
    return Paragraph(escape(shaped).replace("\n", "<br/>"), styles[style])


def code(text):
    return Paragraph(escape(text).replace("\n", "<br/>"), styles["FaCode"])


class GuideTemplate(BaseDocTemplate):
    def __init__(self, filename):
        super().__init__(
            filename, pagesize=A4,
            leftMargin=19 * mm, rightMargin=19 * mm,
            topMargin=21 * mm, bottomMargin=19 * mm,
            title="راهنمای جامع نصب و استفاده از GOFTA V3",
            author="GOFTA | گفتا",
        )
        frame = Frame(
            self.leftMargin, self.bottomMargin,
            self.width, self.height, id="main",
            leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
        )
        self.addPageTemplates([PageTemplate(id="all", frames=[frame], onPage=self.decorate)])

    def decorate(self, canvas, doc):
        canvas.saveState()
        width, height = A4
        canvas.setStrokeColor(colors.HexColor("#dce4ef"))
        canvas.setLineWidth(0.6)
        canvas.line(19 * mm, height - 14 * mm, width - 19 * mm, height - 14 * mm)
        canvas.setFont("Tahoma-Bold", 8)
        canvas.setFillColor(colors.HexColor("#526176"))
        label = get_display(arabic_reshaper.reshape("راهنمای GOFTA V3"))
        canvas.drawRightString(width - 19 * mm, height - 11 * mm, label)
        canvas.line(19 * mm, 14 * mm, width - 19 * mm, 14 * mm)
        canvas.setFont("Tahoma", 8)
        canvas.drawString(19 * mm, 9 * mm, "GOFTA V3")
        canvas.drawRightString(width - 19 * mm, 9 * mm, f"{doc.page}")
        canvas.restoreState()


story = []
story.extend([
    Spacer(1, 25 * mm),
    fa("GOFTA | گفتا", "FaTitle"),
    fa("راهنمای جامع نصب، راه‌اندازی و استفاده", "FaSubtitle"),
    Spacer(1, 8 * mm),
    fa("نسخه ۳ · ویژه ویندوز · فارسی و انگلیسی", "FaSubtitle"),
    Spacer(1, 18 * mm),
    fa(
        "این دفترچه راهنمای قدم‌به‌قدم اجرای برنامه، ساخت حساب، کار با گفتگوها، "
        "مدیریت اعضا و رسانه، تنظیم اعلان‌ها، نگهداری داده‌ها و رفع خطاهای رایج است.",
        "FaBody",
    ),
    Spacer(1, 10 * mm),
    fa(
        "نکته: GOFTA یک پیام‌رسان محلی است. پیش از استفاده، محدودیت‌های نسخه و "
        "آزمون‌های واقعاً انجام‌شده را در انتهای راهنما بخوانید.",
        "FaCallout",
    ),
    Spacer(1, 25 * mm),
    fa("نسخه راهنما: ۱.۰ · ۱ نوامبر ۲۰۲۶", "FaSmall"),
    PageBreak(),
])


def section(title):
    story.append(fa(title, "FaH1"))


def subsection(title):
    story.append(fa(title, "FaH2"))


def para(text):
    story.append(fa(text))


def note(text):
    story.append(fa(text, "FaCallout"))


section("فهرست مطالب")
for item in [
    "۱. آشنایی با برنامه",
    "۲. نصب و راه‌اندازی در ویندوز",
    "۳. ثبت‌نام، ورود و خروج",
    "۴. محیط برنامه و گفتگوها",
    "۵. مخاطبین و جست‌وجو",
    "۶. گروه، کانال و مدیریت اعضا",
    "۷. پیام، عکس، ویدئو و پیام‌های ذخیره‌شده",
    "۸. پروفایل، زبان، ظاهر و اعلان‌ها",
    "۹. فایل‌ها، پشتیبان‌گیری و انتقال",
    "۱۰. رفع اشکال",
    "۱۱. امنیت، محدودیت‌ها و آزمون‌ها",
    "۱۲. راهنمای فنی و ساختار سورس",
]:
    para(item)
para("فهرست برای مرور سریع است؛ شماره صفحه را از شماره‌گذاری پایین هر صفحه پیدا کنید.")
story.append(PageBreak())

section("۱. آشنایی با برنامه")
para(
    "GOFTA V3 برنامه پیام‌رسانی محلی با رابط فارسی راست‌به‌چپ و انگلیسی "
    "چپ‌به‌راست است. رابط وب در مرورگر باز می‌شود، اما برنامه روی رایانه شما "
    "اجرا و داده‌ها به‌طور پیش‌فرض در SQLite و پوشه uploads ذخیره می‌شوند."
)
subsection("امکانات اصلی")
for item in [
    "حساب کاربری با گذرواژه هش‌شده، نام نمایشی، نام کاربری، توضیحات و عکس پروفایل.",
    "گفتگوی خصوصی، گروه و کانال؛ نقش‌های مالک، مدیر و عضو و کنترل اجازه ارسال.",
    "پیام متنی و ارسال تصویر یا ویدئو با ذخیره محلی، نمایش در تاریخچه و مسیر رسانه محافظت‌شده.",
    "دفتر مخاطبین، جست‌وجوی افراد و گفتگوها، وضعیت آنلاین و شمارنده پیام‌های خوانده‌نشده.",
    "تنظیم زبان، حالت روشن/تاریک، فونت فارسی، رنگ‌بندی و اعلان پیام جدید.",
    "مدیریت رسانه‌ها، دانلود و حذف فایل‌های خودتان از گفتگوهای در دسترس.",
]:
    para(item)
note(
    "دسته ربات‌ها فقط یک فیلتر رابط کاربری است؛ ربات واقعی یا اتصال به تلگرام و سرویس بیرونی در این نسخه وجود ندارد."
)

section("۲. نصب و راه‌اندازی در ویندوز")
subsection("پیش‌نیازها")
para(
    "ویندوز و Python 3.10 یا جدیدتر لازم است. هنگام نصب Python گزینه "
    "Add Python to PATH را فعال کنید. برای نصب وابستگی‌ها در اجرای نخست، "
    "اتصال اینترنت لازم است. فایل ZIP را در مسیری که دسترسی نوشتن دارید استخراج کنید."
)
subsection("روش ساده: اجرای run.bat")
para(
    "۱) فایل GOFTA_V3.zip را استخراج کنید. ۲) پوشه GOFTA_V3 را باز کنید. "
    "۳) روی run.bat دوبار کلیک کنید. این فایل به‌ترتیب وارد پوشه پروژه می‌شود، "
    "وابستگی‌های requirements.txt را نصب می‌کند و app.py را اجرا می‌کند. "
    "پنجره را تا پایان استفاده باز نگه دارید."
)
code("GOFTA_V3\\run.bat")
para(
    "اگر نصب وابستگی شکست خورد، متن خطا را در همان پنجره بخوانید؛ معمولاً "
    "Python در PATH نیست یا اتصال اینترنت در دسترس نیست. پس از رفع خطا run.bat "
    "را دوباره اجرا کنید."
)
subsection("بازکردن در مرورگر")
para(
    "بعد از مشاهده پیام اجرای Flask در پنجره، مرورگر را باز کنید و این نشانی را وارد کنید:"
)
code("http://127.0.0.1:5000")
para(
    "برنامه فقط روی رایانه محلی گوش می‌دهد. برای توقف، پنجره اجرا را فعال کرده "
    "و Ctrl+C را بزنید یا آن را ببندید. بستن پنجره سرور را متوقف می‌کند؛ "
    "داده‌های ذخیره‌شده باقی می‌مانند."
)
subsection("اجرای دستی از PowerShell")
para(
    "در PowerShell به پوشه GOFTA_V3 بروید، سپس فرمان‌های زیر را اجرا کنید. "
    "در حالت اجرای دستی، اگر Python با فرمان python شناخته نمی‌شود از py -3 استفاده کنید."
)
code(
    "cd C:\\path\\to\\GOFTA_V3\n"
    "python -m pip install -r requirements.txt\n"
    "python app.py"
)
note(
    "مسیر بالا نمونه است؛ آن را با مسیر واقعی پوشه استخراج‌شده جایگزین کنید. "
    "اگر run.bat کار می‌کند، اجرای دستی لازم نیست."
)

section("۳. ثبت‌نام، ورود و خروج")
subsection("ساخت حساب")
para(
    "بار نخست، صفحه ثبت‌نام نمایش داده می‌شود. نام نمایشی ۲ تا ۶۰ نویسه، "
    "نام کاربری ۳ تا ۳۰ حرف لاتین/عدد/زیرخط، و گذرواژه دست‌کم ۸ نویسه وارد کنید. "
    "شماره تلفن اختیاری است. نام کاربری باید یکتا باشد."
)
subsection("ورود و خروج")
para(
    "در دفعات بعد با نام کاربری و گذرواژه وارد شوید. خروج از حساب از ویرایش پروفایل "
    "در پایین نوار گفتگوها در دسترس است. خروج، حساب یا تاریخچه را حذف نمی‌کند."
)
subsection("ورود با شماره تلفن")
para(
    "برای ورود تلفنی، شماره باید در پروفایل ثبت و با کد تأیید شود. حالت پیش‌فرض "
    "محلی، کد آزمایشی را داخل رابط نشان می‌دهد؛ درگاه پیامکی واقعی پیکربندی نشده است. "
    "ورود تلفنی ابتدا گذرواژه و سپس کد یک‌بارمصرف می‌خواهد."
)
note(
    "کد آزمایشی، پیامک واقعی نیست و برای میزبانی عمومی امن نیست. برای استفاده عمومی "
    "ابتدا درگاه پیامکی واقعی را پیاده‌سازی و حالت آزمایشی را خاموش کنید."
)

section("۴. محیط برنامه و گفتگوها")
subsection("نوار کناری و منوی همبرگری")
para(
    "در نوار سمت راست رابط فارسی، جست‌وجو و دسته‌ها قرار دارند: همه، خوانده‌نشده، "
    "شخصی، گروه‌ها، کانال‌ها، ربات‌ها و ذخیره‌شده. آیکون مداد پایین نوار، ویرایش "
    "پروفایل را باز می‌کند. منوی ☰ میانبر پروفایل، ساخت گروه/کانال، مخاطبین، "
    "پیام‌های ذخیره‌شده، تنظیمات و حالت شب را دارد."
)
subsection("ساخت گفتگوی خصوصی")
para(
    "از دکمه شروع گفتگوی تازه یا منوی همبرگری وارد فرم شوید، نوع «شخصی» را انتخاب "
    "کنید و نام کاربری طرف مقابل را وارد کنید. با انتخاب نتیجه از جست‌وجو نیز "
    "می‌توانید گفتگوی خصوصی را آغاز کنید. گفتگوی خصوصی موجود دوباره استفاده می‌شود."
)
subsection("نشانگرها")
para(
    "آخرین پیام و زمان آن زیر عنوان گفتگو نمایش داده می‌شود. شمارنده عددی پیام‌های "
    "خوانده‌نشده را نشان می‌دهد. باز کردن گفتگو نشانگر خواندن را به‌روز می‌کند. "
    "انتخاب دسته، فقط گفتگوهای همان نوع را نمایش می‌دهد."
)

section("۵. مخاطبین و جست‌وجو")
para(
    "منوی ☰ را باز و «مخاطبین» را انتخاب کنید. از دکمه افزودن مخاطب استفاده کنید، "
    "حداقل دو نویسه از نام یا نام کاربری را بنویسید و افزودن را بزنید. انتخاب یک "
    "مخاطب از فهرست، گفتگوی خصوصی او را باز می‌کند. فهرست بر اساس وضعیت آنلاین "
    "و نام مرتب می‌شود."
)
para(
    "جست‌وجوی بالای فهرست گفتگوها هم گفتگوهای موجود را بر اساس عنوان و متن آخرین پیام "
    "فیلتر می‌کند و هم کاربران را با نام نمایشی یا نام کاربری پیدا می‌کند. انتخاب "
    "نتیجه کاربر گفتگوی خصوصی را باز می‌کند. جست‌وجوی کاربران از دو نویسه به بالا "
    "انجام می‌شود."
)

section("۶. گروه، کانال و مدیریت اعضا")
subsection("ایجاد گروه یا کانال")
para(
    "از منوی ☰ گزینه ایجاد گروه یا کانال را بزنید. نامی با حداقل دو نویسه وارد کنید. "
    "در صورت نیاز نام‌های کاربری اعضا را با ویرگول از هم جدا کنید. سازنده مالک گفتگو "
    "می‌شود. ایجاد کانال با همان فرم است، اما ارسال پیام در کانال فقط برای مالک و مدیر مجاز است."
)
subsection("اعضا، نقش‌ها و حذف")
para(
    "داخل گروه یا کانال، آیکون اعضا را باز کنید. مالک می‌تواند اعضا را حذف و نقش "
    "مدیر/عضو را تغییر دهد. مدیر نیز می‌تواند اعضای عادی را حذف کند، اما نمی‌تواند "
    "مالک یا مدیر دیگر را حذف کند. مالک از گفتگو قابل حذف نیست. کاربر حذف‌شده دیگر "
    "عضو نیست و API گفتگو/رسانه را دریافت نمی‌کند."
)
para(
    "اگر برای تغییر نقش یا حذف عضو مجوز ندارید، با مالک گفتگو تماس بگیرید. "
    "قابلیت ارسال در کانال برای عضو عادی غیرفعال است."
)

section("۷. پیام، عکس، ویدئو و پیام‌های ذخیره‌شده")
subsection("ارسال پیام")
para(
    "گفتگو را باز کنید، متن را در کادر پایین بنویسید و ارسال را بزنید. پیام‌ها در "
    "پایگاه داده ذخیره می‌شوند و اعضای آنلاین از راه Socket.IO پیام تازه را می‌بینند. "
    "تاریخچه پس از خروج از حساب و راه‌اندازی مجدد باقی می‌ماند."
)
subsection("پیوست رسانه")
para(
    "علامت + را بزنید و تصویر یا ویدئو انتخاب کنید. پیش‌نمایش و نام/حجم پیش از ارسال "
    "نمایش داده می‌شود. تصویرهای JPG/JPEG/PNG/WEBP/GIF و ویدئوهای MP4/WEBM/MOV/M4V "
    "پذیرفته می‌شوند. حد پیش‌فرض بارگذاری هر فایل ۶۴ مگابایت است و مالک پروژه می‌تواند "
    "آن را با متغیر محیطی GOFTA_MAX_UPLOAD_MB تغییر دهد."
)
para(
    "فایل‌ها با نام تصادفی روی سرور محلی ذخیره می‌شوند. تصویر با Pillow بررسی می‌شود؛ "
    "ویدئو تا حدی با امضای ظرف فایل اعتبارسنجی می‌شود. دسترسی رسانه به عضویت در گفتگو "
    "وابسته است. عضو غیرمجاز فایل را دریافت نمی‌کند."
)
subsection("پیام‌های ذخیره‌شده")
para(
    "از دسته ذخیره‌شده یا منوی همبرگری به پیام‌های ذخیره‌شده بروید. این فضا برای "
    "نگهداری پیام‌های شخصی است و محل ارسال پیام عادی به خودتان نیست. در گفتگو، "
    "گزینه ذخیره پیام را برای افزودن/برداشتن از ذخیره‌شده‌ها استفاده کنید."
)

section("۸. پروفایل، زبان، ظاهر و اعلان‌ها")
subsection("ویرایش پروفایل")
para(
    "آیکون مداد پایین نوار یا «پروفایل من» در منو را انتخاب کنید. نام نمایشی، توضیحات "
    "و عکس را ویرایش کنید. عکس قبل از ذخیره پیش‌نمایش می‌شود. شماره تلفن اختیاری است؛ "
    "بعد از ارسال کد، آن را در فیلد کد وارد و تأیید کنید. سطح نمایش شماره را روی "
    "فقط خودم، اعضای گفتگوها یا همه بگذارید."
)
subsection("تنظیمات ظاهری")
para(
    "در منوی همبرگری «تنظیمات» را باز کنید. زبان فارسی/انگلیسی، پوسته روشن/تاریک، "
    "فونت فارسی وزیرمتن/فونت دستگاه و یکی از رنگ‌های تم را انتخاب کنید و ذخیره را بزنید. "
    "تنظیمات به حساب شما متصل هستند."
)
subsection("اعلان پیام جدید")
para(
    "در تنظیمات، گزینه اعلان پیام‌های جدید را روشن یا خاموش کنید. برای اعلان دسکتاپ "
    "دکمه اجازه اعلان‌های مرورگر را بزنید و اجازه را در مرورگر تأیید کنید. اعلان پیام "
    "برای گفتگوی دیگری است که در حال حاضر باز نیست؛ پیام خودتان اعلان نمی‌سازد. کلیک "
    "روی اعلان برنامه را به گفتگو می‌برد."
)
note(
    "اگر اجازه اعلان قبلاً در مرورگر رد شده باشد، آن را از تنظیمات سایت در مرورگر "
    "به‌صورت دستی فعال کنید. حالت محلی در http://127.0.0.1 معمولاً مجاز است؛ "
    "اعلان به تنظیمات ویندوز/مرورگر هم وابسته است."
)

section("۹. فایل‌ها، پشتیبان‌گیری و انتقال")
subsection("مدیریت فایل‌ها")
para(
    "از تنظیمات، «مدیریت فایل‌ها» را باز کنید. حجم رسانه‌های قابل دسترسی، نام، گفتگو، "
    "زمان، دانلود و در صورت مالکیت، حذف نمایش داده می‌شود. حذف فایل پیام بدون متن را "
    "حذف می‌کند؛ اگر پیام متن هم داشته باشد، متن می‌ماند و پیوست حذف می‌شود."
)
subsection("مسیر ذخیره‌سازی")
para(
    "پایگاه داده به‌صورت پیش‌فرض در instance/gofta.db و فایل‌های بارگذاری‌شده در "
    "uploads قرار دارند. تصویر پروفایل نیز در زیرپوشه profiles نگهداری می‌شود. فایل "
    "پشتیبان را فقط وقتی برنامه متوقف است از هر دو مسیر بگیرید."
)
code("GOFTA_V3\\instance\\gofta.db\nGOFTA_V3\\uploads\\")
para(
    "برای انتقال نصب به رایانه دیگر، ابتدا برنامه را متوقف کنید، از پوشه instance و "
    "uploads کپی پشتیبان بگیرید، نسخه مقصد را نصب کنید و همین داده‌ها را در مسیرهای "
    "مقصد قرار دهید. از نگهداری پشتیبان در فضای اشتراکی ناامن خودداری کنید."
)

section("۱۰. رفع اشکال")
subsection("صفحه باز نمی‌شود یا اتصال رد شد")
para(
    "پنجره run.bat را بررسی کنید؛ باید باز و بدون خطای توقف باشد. نشانی را دقیقاً "
    "http://127.0.0.1:5000 وارد کنید. اگر پورت 5000 قبلاً اشغال است، برنامه ممکن است "
    "خطای bind بدهد؛ برنامه دیگری را که پورت را گرفته ببندید یا با پشتیبان فنی برای "
    "تغییر پورت هماهنگ کنید."
)
subsection("نصب وابستگی‌ها خطا می‌دهد")
para(
    "در PowerShell دستور python --version و python -m pip --version را اجرا کنید. "
    "اگر Python شناخته نمی‌شود، نصب Python و PATH را اصلاح کنید. برای خطای شبکه، "
    "اتصال اینترنت را برقرار و run.bat را دوباره اجرا کنید. متن خطا را نگه دارید."
)
subsection("پیام زنده نمی‌رسد")
para(
    "از ورود بودن همه طرف‌ها و عضویت در همان گفتگو مطمئن شوید. صفحه را تازه‌سازی کنید "
    "و پنجره سرور را برای خطا بررسی کنید. پیام‌ها در پایگاه داده ذخیره می‌شوند؛ "
    "اتصال زنده به Socket.IO وابسته است."
)
subsection("آپلود تصویر یا ویدئو رد می‌شود")
para(
    "پسوند، نوع فایل، معتبر بودن تصویر/امضای ویدئو و حجم را بررسی کنید. حد پیش‌فرض "
    "۶۴ مگابایت است. بعضی فایل‌های ویدئویی ممکن است امضای قابل قبول داشته باشند اما "
    "codec آن‌ها در مرورگر قابل پخش نباشد."
)
subsection("شماره یا اعلان فعال نمی‌شود")
para(
    "OTP در نسخه محلی آزمایشی است و تنها شماره پذیرفته‌شده، شماره‌ای است که در همین "
    "حساب تأیید شده باشد. برای اعلان، گزینه تنظیمات را روشن کنید و مجوز مرورگر و "
    "تنظیمات Windows Focus/Do not disturb را بررسی کنید."
)

section("۱۱. امنیت، محدودیت‌ها و آزمون‌ها")
para(
    "گذرواژه به‌صورت هش‌شده ذخیره می‌شود. درخواست‌های تغییر داده CSRF دارند. "
    "مسیرهای گفتگو و رسانه عضویت را بررسی می‌کنند و کانال ارسال را به مدیران محدود "
    "می‌کند. شماره تلفن طبق سطح حریم خصوصی انتخاب‌شده نمایش داده می‌شود. این اقدامات "
    "جایگزین ممیزی امنیتی یا استقرار امن نیستند."
)
note(
    "این نسخه برای اجرای محلی یا شبکه مورد اعتماد است، نه میزبانی عمومی آماده. "
    "برای انتشار عمومی، کلید محرمانه تصادفی، HTTPS، پیکربندی عملیاتی، پشتیبان‌گیری، "
    "کنترل دسترسی و درگاه پیامک واقعی لازم است."
)
para(
    "آزمون‌های پروژه در زمان تهیه این راهنما: ۱۳ آزمون یکپارچه، بررسی compileall، "
    "pip check و راه‌اندازی app factory با ۳۳ route موفق بوده‌اند. آزمون مرورگر "
    "برای ثبت‌نام، گفتگو، گروه/کانال، پیام، جست‌وجو، تصویر، مخاطبین، حذف عضو و "
    "ترجیحات اعلان ثبت شده است. جزئیات دقیق در TEST_REPORT.txt قرار دارد."
)
para(
    "ویدئو در آزمون خودکار با امضای MP4 و پاسخ نوع video/mp4 بررسی شده، اما پخش واقعی "
    "codec در مرورگر تأیید نشده است. پیامک واقعی ارسال نشده است. اعلان با شبیه‌ساز "
    "مرورگر بررسی شده و نمایش بومی سیستم‌عامل به مجوز واقعی وابسته است. تست بار هم‌زمان "
    "و تست نفوذ امنیتی انجام نشده‌اند."
)

section("۱۲. راهنمای فنی و ساختار سورس")
for item in [
    "app.py: نقطه شروع برنامه و راه‌اندازی Flask-SocketIO.",
    "config.py: مسیر پایگاه داده و uploads، کلید برنامه و حد حجم بارگذاری.",
    "app/__init__.py: app factory، راه‌اندازی SQLAlchemy، CSRF و رخدادهای Socket.IO.",
    "app/models.py: مدل کاربران، گفتگوها، اعضا، پیام‌ها، مخاطبین و OTP.",
    "app/routes/auth.py: ثبت‌نام، ورود، OTP آزمایشی و خروج.",
    "app/routes/chat.py: API گفتگو، پیام، رسانه، عضو، مخاطب و فایل.",
    "app/routes/profile.py: پروفایل، تنظیمات و تأیید شماره.",
    "app/services/: منطق گفتگو، اعتبارسنجی/ذخیره رسانه و OTP.",
    "app/templates/: صفحات HTML ورود، ثبت‌نام و برنامه.",
    "app/static/: CSS و JavaScript رابط کاربری.",
    "tests/test_app.py: آزمون‌های یکپارچه.",
    "README.txt و TEST_REPORT.txt: نصب، امکانات و شواهد آزمون.",
]:
    para(item)
subsection("تنظیمات محیطی")
para(
    "GOFTA_SECRET_KEY کلید نشست‌هاست؛ مقدار پیش‌فرض فقط برای اجرای محلی نمونه است. "
    "GOFTA_MAX_UPLOAD_MB حد اندازه فایل به مگابایت است و مقدار پیش‌فرض ۶۴ است. "
    "GOFTA_SMS_TEST_MODE در حالت پیش‌فرض روشن است و کد را در رابط محلی نشان می‌دهد."
)
code(
    "GOFTA_SECRET_KEY=<random-secret>\n"
    "GOFTA_MAX_UPLOAD_MB=64\n"
    "GOFTA_SMS_TEST_MODE=1"
)

story.append(Spacer(1, 8 * mm))
note(
    "برای راه‌اندازی معمولی، همین سه کار کافی است: ZIP را استخراج کنید، run.bat را اجرا کنید، "
    "و به http://127.0.0.1:5000 بروید. برای اطمینان از وضعیت نسخه، TEST_REPORT.txt را بخوانید."
)

doc = GuideTemplate(str(OUTPUT))
doc.build(story)
print(f"Created {OUTPUT}")
