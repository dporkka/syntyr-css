"""Deterministic viewport sweep and representative localized test content."""
from responsive_boundaries import MEDIA, adjacent_pixels
from responsive_viewports import CANONICAL_VIEWPORTS


def sweep_widths():
    widths = set(range(320, 2561, 32))
    widths.update(w for _, w, _ in CANONICAL_VIEWPORTS)
    for _, query, rem, _ in MEDIA:
        if "width" in query:
            widths.update(w for w in adjacent_pixels(rem) if 320 <= w <= 2560)
    return tuple(sorted(widths))


# Test data, not a translation catalog. Identifiers deliberately have no breaks.
CONTENT_CASES = (
    ("de", "ltr", "Benachrichtigungseinstellungen für das Kundenkonto",
     "Änderungen überprüfen und Einstellungen speichern", "Kundenkontoverwaltungseinstellungen" * 3),
    ("pt-BR", "ltr", "Preferências de notificações da conta do cliente",
     "Revisar alterações e salvar configurações", "Identificadordaconfiguraçãodocadastro" * 3),
    ("ar", "rtl", "إعدادات الإشعارات الخاصة بحساب العميل",
     "مراجعة التغييرات وحفظ إعدادات الحساب", "معرفإعداداتحسابالعميل" * 5),
    ("he", "rtl", "הגדרות ההתראות עבור חשבון הלקוח",
     "בדיקת השינויים ושמירת הגדרות החשבון", "מזהההגדרותחשבוןהלקוח" * 5),
)
