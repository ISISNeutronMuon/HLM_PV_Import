from PyQt5.QtGui import QCloseEvent, QShowEvent
from PyQt5.QtWidgets import QDialog, QMessageBox, QSpinBox, QDialogButtonBox, QLabel, QCheckBox
from PyQt5 import uic
from ServiceManager.constants import general_settings_ui
from ServiceManager.settings import Settings


class UIGeneralSettings(QDialog):
    def __init__(self):
        super(UIGeneralSettings, self).__init__()
        uic.loadUi(uifile=general_settings_ui, baseinstance=self)

        self._settings_changed = False

        # region Get widgets
        self.default_meas_update_interval_sb = self.findChild(QSpinBox, 'measUpdateIntervalSpinBox')
        self.check_pv_on_new_entry_cb = self.findChild(QCheckBox, 'autoCheckPVConnection')
        self.auto_load_existing_config_cb = self.findChild(QCheckBox, 'autoLoadExistingConfig')

        self.message_lbl = self.findChild(QLabel, 'message_lbl')

        self.button_box = self.findChild(QDialogButtonBox, 'buttonBox')
        self.apply_btn = self.button_box.button(QDialogButtonBox.Apply)
        # endregion

        # region Connect signals to slots
        self.default_meas_update_interval_sb.valueChanged.connect(lambda _: self.settings_changed(True))
        self.check_pv_on_new_entry_cb.stateChanged.connect(lambda _: self.settings_changed(True))
        self.auto_load_existing_config_cb.stateChanged.connect(lambda _: self.settings_changed(True))

        self.button_box.rejected.connect(self.on_rejected)
        self.button_box.accepted.connect(self.on_accepted)
        self.apply_btn.clicked.connect(self.on_apply)
        # endregion

    def apply_new_settings(self):
        Settings.Manager.set_default_meas_update_interval(self.default_meas_update_interval_sb.value())
        Settings.Manager.set_new_entry_auto_pv_check(self.check_pv_on_new_entry_cb.isChecked())
        Settings.Manager.set_auto_load_existing_config(self.auto_load_existing_config_cb.isChecked())

    def update_fields(self):
        self.default_meas_update_interval_sb.setValue(Settings.Manager.get_default_meas_update_interval())
        self.check_pv_on_new_entry_cb.setChecked(Settings.Manager.get_new_entry_auto_pv_check())
        self.auto_load_existing_config_cb.setChecked(Settings.Manager.get_auto_load_existing_config())
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
        if self._settings_changed:
            quit_msg = "Any changes will be lost. Cancel anyway?"
            reply = QMessageBox.question(self, 'HLM PV Import',
                                         quit_msg, QMessageBox.Yes, QMessageBox.No)

            if reply == QMessageBox.Yes:
                event.accept()
            else:
                event.ignore()

    def showEvent(self, event: QShowEvent):
        self.update_fields()

    def settings_changed(self, changed=True):
        self._settings_changed = changed
        self.apply_btn.setEnabled(changed)
