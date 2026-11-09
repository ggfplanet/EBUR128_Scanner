import unittest
from PySide6.QtCore import QSettings
from ui.i18n import (
    detect_system_language,
    init_language,
    get_current_lang,
    set_current_lang,
    tr,
    SETTINGS_ORG,
    SETTINGS_APP,
)


class TestI18n(unittest.TestCase):
    def setUp(self):
        self.settings = QSettings(SETTINGS_ORG, SETTINGS_APP)
        self.original_saved = self.settings.value("language")
        self.original_current = get_current_lang()

    def tearDown(self):
        if self.original_saved is not None:
            self.settings.setValue("language", self.original_saved)
        else:
            self.settings.remove("language")
        set_current_lang(self.original_current, persist=False)

    def test_detect_system_language_returns_valid_lang(self):
        lang = detect_system_language()
        self.assertIn(lang, ["de", "en"])

    def test_persistence_with_qsettings(self):
        set_current_lang("en", persist=True)
        self.assertEqual(self.settings.value("language"), "en")
        self.assertEqual(get_current_lang(), "en")
        self.assertEqual(tr("select_file"), "Select File")

        set_current_lang("de", persist=True)
        self.assertEqual(self.settings.value("language"), "de")
        self.assertEqual(get_current_lang(), "de")
        self.assertEqual(tr("select_file"), "Datei Auswählen")

    def test_init_language_respects_saved_settings(self):
        self.settings.setValue("language", "en")
        loaded = init_language()
        self.assertEqual(loaded, "en")
        self.assertEqual(get_current_lang(), "en")

        self.settings.setValue("language", "de")
        loaded = init_language()
        self.assertEqual(loaded, "de")
        self.assertEqual(get_current_lang(), "de")

