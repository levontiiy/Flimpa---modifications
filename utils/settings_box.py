from PySide6.QtWidgets import (QLabel, QHBoxLayout, QLineEdit, QGroupBox, QGridLayout, QSizePolicy,
                               QVBoxLayout, QWidget, QComboBox, QPushButton, QFileDialog, QScrollArea)
from PySide6.QtCore import Qt

from utils.shared_data import SharedData
from utils.colormaps import LIFETIME_CMAP_PRESETS, clear_custom_colormap_cache

class TabSettingsWidgets():
    """Visualisation settings shown inside each image tab after analysis.

    Colormap controls (lifetime_cmap / lifetime_cmap_file) appear on Lifetime maps
    and Gallery (tau). Changing them refreshes the current lifetime display.
    """
    def __init__(self, main_window):
        self.shared_info = SharedData()
        self.main_window = main_window
        self.widget_dict = {}  # Dictionary to store references to widgets by param_id
        self.helpers = self.main_window.helpers # import helper functions

    def input_parameters(self, param_name, input_type="lineedit", param_id="", items=[], plot_type=None):
        label = QLabel(str(param_name))
        label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        if plot_type != None:
            if plot_type  == "tau_map":
                plot_id = "tau"
            else:
                plot_id = plot_type
            unique_param_id = f"{plot_id}_{param_id}" if plot_type else param_id

        h_layout_parameters = QHBoxLayout()
        h_layout_parameters.addWidget(label)

        if input_type == "lineedit":
            input_widget = QLineEdit()
            input_widget.setFixedWidth(80)
            input_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
            input_widget.setAlignment(Qt.AlignCenter)
            input_widget.setText(str(self.shared_info.config.get(param_id)))
            input_widget.editingFinished.connect(self.update_img(input_type, input_widget, param_id, plot_type))
            input_widget.setStyleSheet("""QLineEdit { 
                                        background-color: rgb(63, 63, 63);
                                        color: white; }""")
            h_layout_parameters.addWidget(input_widget)
            if plot_type != None:
                self.widget_dict[unique_param_id] = input_widget  # Store widget reference

        elif input_type == "combobox":
            input_widget = QComboBox()
            input_widget.addItems(items)
            input_widget.setFixedWidth(80)
            input_widget.setEditable(True)  # Set editable to False
            input_widget.lineEdit().setAlignment(Qt.AlignCenter)
            input_widget.currentIndexChanged.connect(self.update_img(input_type, input_widget, param_id, plot_type))
            input_widget.setStyleSheet("""QComboBox { 
                                       background-color: rgb(63, 63, 63);
                                       color: white; }""")
            h_layout_parameters.addWidget(input_widget)
            if plot_type != None:
                self.widget_dict[unique_param_id] = input_widget  # Store widget reference

        return h_layout_parameters
    
    def table_settings_input(self, param_name, items=[]):
        label = QLabel(str(param_name))
        label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        h_layout_parameters = QHBoxLayout()
        h_layout_parameters.addWidget(label)

        input_widget = QComboBox()
        input_widget.addItems(items)
        input_widget.setFixedWidth(80)
        input_widget.setEditable(False)
        input_widget.currentIndexChanged.connect(self.helpers.update_table_widget)
        input_widget.setStyleSheet("""QComboBox { 
                                    background-color: rgb(63, 63, 63);
                                    color: white; }""")
        h_layout_parameters.addWidget(input_widget)

        self.widget_dict["table_Group by"] = input_widget

        return h_layout_parameters

    def colormap_settings(self, plot_type):
        """Preset dropdown + custom file picker; writes shared_info.config lifetime_cmap keys."""
        plot_id = "tau" if plot_type == "tau_map" else plot_type

        preset_label = QLabel("Colormap")
        preset_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        preset_combo = QComboBox()
        preset_combo.addItems(LIFETIME_CMAP_PRESETS + ["Custom"])
        preset_combo.setFixedWidth(120)
        preset_combo.setEditable(False)
        preset_combo.setCurrentText(self.shared_info.config.get("lifetime_cmap", "Rainbow"))
        preset_combo.setStyleSheet("""QComboBox {
                                       background-color: rgb(63, 63, 63);
                                       color: white; }""")

        browse_button = QPushButton("Load custom...")
        browse_button.setStyleSheet("QPushButton { color: white; }")

        file_label = QLabel("Custom file")
        file_path = QLineEdit()
        file_path.setReadOnly(True)
        cmap_file = self.shared_info.config.get("lifetime_cmap_file", "None")
        file_path.setText("" if cmap_file in (None, "None") else cmap_file)
        file_path.setStyleSheet("""QLineEdit {
                                        background-color: rgb(63, 63, 63);
                                        color: white; }""")

        self.widget_dict[f"{plot_id}_lifetime_cmap"] = preset_combo
        self.widget_dict[f"{plot_id}_lifetime_cmap_file"] = file_path

        def on_preset_changed():
            name = preset_combo.currentText()
            self.shared_info.config["lifetime_cmap"] = name
            self.sync_widgets("lifetime_cmap", name)
            self._refresh_lifetime_visuals(plot_type, "lifetime_cmap")

        def on_browse():
            path, _ = QFileDialog.getOpenFileName(
                self.main_window,
                "Select custom colormap",
                "",
                "Colormap files (*.csv *.txt *.png *.jpg *.jpeg *.tif *.tiff);;All files (*)",
            )
            if not path:
                return
            clear_custom_colormap_cache()
            self.shared_info.config["lifetime_cmap_file"] = path
            self.shared_info.config["lifetime_cmap"] = "Custom"
            preset_combo.blockSignals(True)
            preset_combo.setCurrentText("Custom")
            preset_combo.blockSignals(False)
            file_path.setText(path)
            self.sync_widgets("lifetime_cmap", "Custom")
            for key, widget in self.widget_dict.items():
                if key.endswith("lifetime_cmap_file") and isinstance(widget, QLineEdit):
                    widget.setText(path)
            self._refresh_lifetime_visuals(plot_type, "lifetime_cmap_file")

        preset_combo.currentIndexChanged.connect(on_preset_changed)
        browse_button.clicked.connect(on_browse)

        preset_row = QHBoxLayout()
        preset_row.addWidget(preset_label)
        preset_row.addWidget(preset_combo)
        preset_row.addWidget(browse_button)

        file_row = QHBoxLayout()
        file_row.addWidget(file_label)
        file_row.addWidget(file_path, 1)

        wrapper = QVBoxLayout()
        wrapper.addLayout(preset_row)
        wrapper.addLayout(file_row)
        return wrapper

    def _refresh_lifetime_visuals(self, plot_type, param_id):
        if param_id not in ("lifetime_cmap", "lifetime_cmap_file", "lifetime_vmin", "lifetime_vmax",
                            "lifetime_map", "lifetime_itegrate"):
            return

        if plot_type == "tau_map":
            self.main_window.plotImages.plot_tau_map()
            if param_id != "lifetime_itegrate":
                self.main_window.phasor_componets.plot_phasor_coordinates()
        elif plot_type == "gallery":
            self.main_window.plotImages.gallery_imgs(data_dict=self.shared_info.results_dict)
            if getattr(self.main_window.phasor_componets, "_is_gallery_active", lambda: False)():
                if self.shared_info.phasor_settings["plot_type"] == "individual":
                    self.main_window.phasor_componets.plot_phasor_gallery_individual(
                        data_dict=self.shared_info.results_dict
                    )
                else:
                    self.main_window.phasor_componets.plot_phasor_gallery_condition(
                        data_dict=self.shared_info.results_dict
                    )

    def update_img(self, input_type, input_widget, param_id, plot_type):
        def action_wrapper():
            if input_type == "lineedit":
                text = input_widget.text()
            elif input_type == "combobox":
                text = input_widget.currentText()
            
            self.update_parameters(param_id, text, plot_type)
            self.sync_widgets(param_id, text)
            
        return action_wrapper
    
    def sync_widgets(self, param_id, text):
        for key, widget in self.widget_dict.items():
            key_split = key.split("_")
            key_id = key_split[-2] + "_" + key_split[-1]
    
            if key_id == param_id:
                current_text = widget.text() if isinstance(widget, QLineEdit) else widget.currentText()
                if current_text != text:
                    widget.blockSignals(True)
                    if isinstance(widget, QLineEdit):
                        widget.setText(text)
                    elif isinstance(widget, QComboBox):
                        widget.setCurrentText(text)
                    widget.blockSignals(False)

    def update_parameters(self, param_id, text, plot_type):
        self.shared_info.config[param_id] = text
       
        if self.shared_info.config["selected_file"] == None:
            filename = list(self.shared_info.raw_data_dict.keys())[-1]
        else:
            filename = self.shared_info.config["selected_file"]

        if filename in self.shared_info.intensity_img_dict:
            if param_id.split("_")[1] == "int":
                self.main_window.plotImages.gallery_imgs_I(data_dict=self.shared_info.results_dict)
            elif param_id.split("_")[0] == "lifetime":
                self._refresh_lifetime_visuals(plot_type, param_id)
            elif param_id == "tau_violin":
                self.main_window.plotImages.violin_plots()

    def input_box(self):
        grid_parameters = QGridLayout()
        grid_parameters.setHorizontalSpacing(6)
        grid_parameters.setVerticalSpacing(6)
        grid_parameters.addLayout(self.input_parameters(param_name="Min. intensity", param_id="vmin_int"), 0, 0)
        grid_parameters.addLayout(self.input_parameters(param_name="Max. intensity", param_id="vmax_int" ), 0, 1)
        return grid_parameters
    
    def lifetime_box(self):
        grid_parameters = QGridLayout()
        grid_parameters.setHorizontalSpacing(6)
        grid_parameters.setVerticalSpacing(6)
        grid_parameters.addLayout(self.input_parameters(param_name="Min. lifetime (ns)", param_id="lifetime_vmin", plot_type = "tau_map"), 0, 0)
        grid_parameters.addLayout(self.input_parameters(param_name="Max. lifetime (ns)", param_id="lifetime_vmax", plot_type = "tau_map"), 0, 1)
        grid_parameters.addLayout(self.input_parameters(param_name="Lifetime map", input_type="combobox", items=["average", "M", "phi"], param_id="lifetime_map", plot_type = "tau_map"), 1, 0)
        grid_parameters.addLayout(self.input_parameters(param_name="Integrate itensity", input_type="combobox", items=["False", "True"], param_id="lifetime_itegrate", plot_type = "tau_map"), 1, 1)
        grid_parameters.addLayout(self.colormap_settings("tau_map"), 2, 0, 1, 2)
        return grid_parameters
    
    def gallery_box(self):
        grid_parameters = QGridLayout()
        grid_parameters.setHorizontalSpacing(6)
        grid_parameters.setVerticalSpacing(6)
        grid_parameters.addLayout(self.input_parameters(param_name="Min. lifetime (ns)", param_id="lifetime_vmin", plot_type = "gallery"), 0, 0)
        grid_parameters.addLayout(self.input_parameters(param_name="Max. lifetime (ns)", param_id="lifetime_vmax", plot_type = "gallery"), 0, 1)
        grid_parameters.addLayout(self.input_parameters(param_name="Lifetime map", input_type="combobox", items=["average", "M", "phi"], param_id="lifetime_map", plot_type = "gallery"), 1, 0)
        grid_parameters.addLayout(self.input_parameters(param_name="Integrate itensity", input_type="combobox", items=["False", "True"], param_id="lifetime_itegrate", plot_type = "gallery"), 1, 1)
        grid_parameters.addLayout(self.colormap_settings("gallery"), 2, 0, 1, 2)
        return grid_parameters
    
    def violin_box(self):
        grid_parameters = QGridLayout()
        grid_parameters.setHorizontalSpacing(6)
        grid_parameters.setVerticalSpacing(6)
        grid_parameters.addLayout(self.input_parameters(param_name="Lifetime map", input_type="combobox", items=["average", "M", "phi"], param_id="tau_violin", plot_type = "violin"), 0, 0)
        return grid_parameters
    
    def table_box(self):
        grid_parameters = QGridLayout()
        grid_parameters.setHorizontalSpacing(6)
        grid_parameters.setVerticalSpacing(6)
        grid_parameters.addLayout(self.table_settings_input(param_name="Group by", 
                                                        items=["None", "Condition", "Sample"]), 0, 0)
        return grid_parameters
    
    def input_layout(self, box_type):
        input_group_box = QGroupBox("Settings")
        
        if box_type == 'input_box':
            input_group_box.setLayout(self.input_box())
        elif box_type == 'lifetime_box':
            input_group_box.setLayout(self.lifetime_box())
        elif box_type == 'gallery_box':
            input_group_box.setLayout(self.gallery_box())
        elif box_type == 'violin_box':
            input_group_box.setLayout(self.violin_box())
        elif box_type == 'table_box':
            input_group_box.setLayout(self.table_box())
        
        input_group_box.setStyleSheet("""
            QGroupBox {
                background-color: rgb(18, 18, 18);
                border: 1px solid rgb(40, 40, 40);
                border-radius: 4px;
                margin-top:10 px;                                               
                padding: 10px;                         
                }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 2px;
                color: rgb(255, 255, 255);
            }""")

        scroll = QScrollArea()
        scroll.setWidget(input_group_box)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setMaximumHeight(220)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        v_input_layout = QVBoxLayout()
        v_input_layout.addWidget(scroll)
        
        h_tab_settings = QHBoxLayout()
        h_tab_settings.addStretch(1)
        h_tab_settings.addLayout(v_input_layout) 
        h_tab_settings.addStretch(1)
    
        return h_tab_settings
