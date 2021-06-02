from PyQt5.QtGui import QCloseEvent, QShowEvent
from PyQt5.QtWidgets import QDialog, QDialogButtonBox
from PyQt5 import uic
from ServiceManager.constants import general_settings_ui
from ServiceManager.settings import Settings
from ServiceManager.utilities import apply_unsaved_changes_dialog


class UIGeneralSettings(QDialog):
    def __init__(self):
        super(UIGeneralSettings, self).__init__()
        uic.loadUi(uifile=general_settings_ui, baseinstance=self)

        self._settings_changed = False

        self.apply_btn = self.button_box.button(QDialogButtonBox.Apply)

        # region Connect signals to slots
        self.default_meas_update_interval_sb.valueChanged.connect(lambda _: self.settings_changed(True))
        self.check_pv_on_new_entry_cb.stateChanged.connect(lambda _: self.settings_changed(True))
        self.auto_load_existing_config_cb.stateChanged.connect(lambda _: self.settings_changed(True))

        self.button_box.rejected.connect(self.on_rejected)
        self.button_box.accepted.connect(self.on_accepted)
        self.apply_btn.clicked.connect(self.on_apply)
        # endregion

    def apply_new_settings(self):
        Settings.Manager.default_update_interval = self.default_meas_update_interval_sb.value()
        Settings.Manager.auto_pv_check = self.check_pv_on_new_entry_cb.isChecked()
        Settings.Manager.auto_load_existing_config = self.auto_load_existing_config_cb.isChecked()

    def update_fields(self):
        self.default_meas_update_interval_sb.setValue(Settings.Manager.default_update_interval)
        self.check_pv_on_new_entry_cb.setChecked(Settings.Manager.auto_pv_check)
        self.auto_load_existing_config_cb.setChecked(Settings.Manager.auto_load_existing_config)
        self.message_lbl.clear()
        self.settings_changed(False)

    def on_accepted(self):
        if self._settings_changed:
            self.on_apply()
        self.close()

    def on_rejected(self):
        self.close()

    def on_apply(self):
        self.apply_new_settings()
        self.update_fields()
        self.message_lbl.setText('Settings updated.')

    def closeEvent(self, event: QCloseEvent):
        apply_unsaved_changes_dialog(event, self.apply_new_settings, self._settings_changed)

    def showEvent(self, event: QShowEvent):
        self.update_fields()

    def settings_changed(self, changed=True):
        self._settings_changed = changed
        self.apply_btn.setEnabled(changed)
