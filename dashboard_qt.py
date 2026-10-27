#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
import time
import json
from collections import deque
from datetime import datetime

import serial
import serial.tools.list_ports
import pandas as pd
import numpy as np

from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize
from PyQt6.QtGui import QColor, QFont, QIcon, QAction
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QLabel, QPushButton, QComboBox, QCheckBox,
    QGroupBox, QTabWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QFileDialog, QMessageBox, QSplitter, QProgressBar,
    QPlainTextEdit, QFrame
)

import pyqtgraph as pg

pg.setConfigOption("background", "#0f172a")
pg.setConfigOption("foreground", "#94a3b8")
pg.setConfigOption("antialias", True)


class SerialWorker(QThread):
    data_received = pyqtSignal(dict)
    raw_line_received = pyqtSignal(str)
    connection_status = pyqtSignal(bool, str)

    def __init__(self, port="COM9", baudrate=115200):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self._running = True
        self._serial = None

    def run(self):
        try:
            self._serial = serial.Serial(self.port, self.baudrate, timeout=1.0)
            self._serial.setDTR(False)
            self._serial.setRTS(True)
            time.sleep(0.1)
            self._serial.setRTS(False)
            time.sleep(0.5)
            self._serial.reset_input_buffer()
            self.connection_status.emit(True, f"Conectado a {self.port} ({self.baudrate} bps)")
        except Exception as e:
            self.connection_status.emit(False, f"Falha na conexão serial: {str(e)}")
            return

        while self._running:
            try:
                line = self._serial.readline().decode("utf-8", errors="replace").strip()
                if not line:
                    continue

                self.raw_line_received.emit(line)

                if line.startswith("{") and line.endswith("}"):
                    try:
                        data = json.loads(line)
                        data["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        data["epoch"] = time.time()
                        self.data_received.emit(data)
                    except json.JSONDecodeError:
                        pass
            except Exception as e:
                self.connection_status.emit(False, f"Erro de leitura na porta {self.port}: {str(e)}")
                break

        if self._serial and self._serial.is_open:
            self._serial.close()
            self.connection_status.emit(False, "Porta serial desconectada")

    def stop(self):
        self._running = False
        self.wait(1500)


class MetricCard(QFrame):
    def __init__(self, title, unit="", accent_color="#38bdf8", parent=None):
        super().__init__(parent)
        self.title = title
        self.unit = unit
        self.accent_color = accent_color

        self.setObjectName("MetricCard")
        self.setStyleSheet(f"""
            #MetricCard {{
                background-color: #1e293b;
                border: 1px solid #334155;
                border-left: 4px solid {accent_color};
                border-radius: 8px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(2)

        h_layout = QHBoxLayout()
        self.lbl_title = QLabel(title.upper())
        self.lbl_title.setStyleSheet("color: #94a3b8; font-size: 10px; font-weight: bold; letter-spacing: 0.5px;")
        self.lbl_badge = QLabel("---")
        self.lbl_badge.setStyleSheet(f"background-color: {accent_color}22; color: {accent_color}; border-radius: 4px; padding: 2px 6px; font-size: 10px; font-weight: bold;")
        h_layout.addWidget(self.lbl_title)
        h_layout.addStretch()
        h_layout.addWidget(self.lbl_badge)
        layout.addLayout(h_layout)

        val_layout = QHBoxLayout()
        self.lbl_value = QLabel("--.-")
        self.lbl_value.setStyleSheet("color: #f8fafc; font-size: 22px; font-weight: bold;")
        self.lbl_unit = QLabel(unit)
        self.lbl_unit.setStyleSheet("color: #64748b; font-size: 12px; font-weight: normal; margin-bottom: 2px;")
        val_layout.addWidget(self.lbl_value)
        val_layout.addWidget(self.lbl_unit, alignment=Qt.AlignmentFlag.AlignBottom)
        val_layout.addStretch()
        layout.addLayout(val_layout)

        self.lbl_stats = QLabel("Mín: -- | Méd: -- | Máx: --")
        self.lbl_stats.setStyleSheet("color: #64748b; font-size: 10px;")
        layout.addWidget(self.lbl_stats)

    def update_value(self, value, cur_str=None, badge=None, min_v=None, avg_v=None, max_v=None):
        if cur_str:
            self.lbl_value.setText(cur_str)
        elif isinstance(value, (int, float)):
            self.lbl_value.setText(f"{value:.1f}")
        else:
            self.lbl_value.setText(str(value))

        if badge is not None:
            self.lbl_badge.setText(str(badge))

        if min_v is not None and avg_v is not None and max_v is not None:
            self.lbl_stats.setText(f"Mín: {min_v:.1f} | Méd: {avg_v:.1f} | Máx: {max_v:.1f}")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ESP32-C5 Bancada - Telemetria e Análise Sensorial")
        self.resize(1366, 900)

        self.history = deque(maxlen=5000)
        self.serial_worker = None
        self.is_recording = True

        self.apply_theme()
        self.init_ui()

        self.ui_timer = QTimer()
        self.ui_timer.timeout.connect(self.update_plots_and_kpis)
        self.ui_timer.start(500)

    def apply_theme(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #090d16;
            }
            QWidget {
                color: #e2e8f0;
                font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
            }
            QGroupBox {
                background-color: #111827;
                border: 1px solid #1f2937;
                border-radius: 8px;
                margin-top: 12px;
                font-size: 11px;
                font-weight: bold;
                color: #9ca3af;
                padding: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 4px;
            }
            QComboBox, QPushButton {
                background-color: #1e293b;
                border: 1px solid #334155;
                border-radius: 6px;
                color: #f1f5f9;
                padding: 6px 12px;
                font-size: 12px;
                font-weight: 500;
            }
            QComboBox:hover, QPushButton:hover {
                background-color: #273548;
                border-color: #475569;
            }
            QPushButton#btnConnect {
                background-color: #0284c7;
                border-color: #0ea5e9;
                color: #ffffff;
                font-weight: bold;
            }
            QPushButton#btnConnect:hover {
                background-color: #0369a1;
            }
            QPushButton#btnExport {
                background-color: #059669;
                border-color: #10b981;
                color: #ffffff;
                font-weight: bold;
            }
            QPushButton#btnExport:hover {
                background-color: #047857;
            }
            QTabWidget::pane {
                border: 1px solid #1e293b;
                background-color: #0f172a;
                border-radius: 6px;
            }
            QTabBar::tab {
                background-color: #1e293b;
                color: #94a3b8;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                font-size: 11px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background-color: #0f172a;
                color: #38bdf8;
                border-bottom: 2px solid #38bdf8;
            }
            QTableWidget {
                background-color: #0f172a;
                gridline-color: #1e293b;
                border: 1px solid #1e293b;
                border-radius: 4px;
                font-size: 11px;
            }
            QHeaderView::section {
                background-color: #1e293b;
                color: #94a3b8;
                padding: 4px 6px;
                border: 1px solid #0f172a;
                font-weight: bold;
                font-size: 11px;
            }
            QPlainTextEdit {
                background-color: #0b0f19;
                border: 1px solid #1e293b;
                color: #38bdf8;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
            }
        """)

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 14, 16, 14)
        main_layout.setSpacing(12)

        main_layout.addLayout(self.create_control_toolbar())
        main_layout.addLayout(self.create_kpi_cards())

        self.splitter = QSplitter(Qt.Orientation.Vertical)
        self.splitter.addWidget(self.create_charts_area())
        self.splitter.addWidget(self.create_bottom_tabs())
        self.splitter.setCollapsible(0, False)
        self.splitter.setCollapsible(1, False)
        self.splitter.setSizes([380, 270])
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 1)

        main_layout.addWidget(self.splitter)

    def create_control_toolbar(self):
        layout = QHBoxLayout()
        layout.setSpacing(10)

        lbl_port = QLabel("Porta Serial:")
        lbl_port.setStyleSheet("color: #94a3b8; font-weight: bold; font-size: 11px;")
        self.cb_ports = QComboBox()
        self.cb_ports.setMinimumWidth(120)
        self.refresh_serial_ports()

        btn_refresh = QPushButton("🔄")
        btn_refresh.setToolTip("Atualizar portas COM disponíveis")
        btn_refresh.clicked.connect(self.refresh_serial_ports)

        lbl_baud = QLabel("Baud:")
        lbl_baud.setStyleSheet("color: #94a3b8; font-weight: bold; font-size: 11px;")
        self.cb_baud = QComboBox()
        self.cb_baud.addItems(["115200", "9600", "57600", "230400"])

        self.btn_connect = QPushButton("Conectar")
        self.btn_connect.setObjectName("btnConnect")
        self.btn_connect.clicked.connect(self.toggle_connection)

        self.lbl_status = QLabel("Desconectado")
        self.lbl_status.setStyleSheet("background-color: #ef444422; color: #f87171; border: 1px solid #ef444455; border-radius: 4px; padding: 4px 8px; font-weight: bold; font-size: 11px;")

        layout.addWidget(lbl_port)
        layout.addWidget(self.cb_ports)
        layout.addWidget(btn_refresh)
        layout.addWidget(lbl_baud)
        layout.addWidget(self.cb_baud)
        layout.addWidget(self.btn_connect)
        layout.addWidget(self.lbl_status)
        layout.addStretch()

        self.btn_export_csv = QPushButton("📥 Exportar CSV")
        self.btn_export_csv.setObjectName("btnExport")
        self.btn_export_csv.clicked.connect(lambda: self.export_data("csv"))

        self.btn_export_excel = QPushButton("📊 Exportar Excel")
        self.btn_export_excel.setObjectName("btnExport")
        self.btn_export_excel.clicked.connect(lambda: self.export_data("excel"))

        self.btn_export_json = QPushButton("📄 JSON")
        self.btn_export_json.clicked.connect(lambda: self.export_data("json"))

        self.btn_clear = QPushButton("🗑️ Limpar")
        self.btn_clear.clicked.connect(self.clear_history)

        self.btn_about = QPushButton("ℹ️ Sobre")
        self.btn_about.clicked.connect(self.show_about_dialog)

        layout.addWidget(self.btn_export_csv)
        layout.addWidget(self.btn_export_excel)
        layout.addWidget(self.btn_export_json)
        layout.addWidget(self.btn_clear)
        layout.addWidget(self.btn_about)

        return layout

    def create_kpi_cards(self):
        layout = QHBoxLayout()
        layout.setSpacing(12)

        self.card_co2 = MetricCard("Dióxido de Carbono (CO2)", "ppm", accent_color="#10b981")
        self.card_temp = MetricCard("Temperatura", "°C", accent_color="#f97316")
        self.card_hum = MetricCard("Umidade Relativa", "%", accent_color="#06b6d4")
        self.card_press = MetricCard("Pressão Barométrica", "hPa", accent_color="#8b5cf6")
        self.card_sys = MetricCard("Status do Sistema", "RISC-V", accent_color="#38bdf8")

        layout.addWidget(self.card_co2)
        layout.addWidget(self.card_temp)
        layout.addWidget(self.card_hum)
        layout.addWidget(self.card_press)
        layout.addWidget(self.card_sys)

        return layout

    def create_charts_area(self):
        container = QWidget()
        grid = QGridLayout(container)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(10)

        self.plot_co2 = pg.PlotWidget(title="<b style='color:#10b981; font-size:12px;'>Dióxido de Carbono (CO2)</b>")
        self.plot_co2.showGrid(x=True, y=True, alpha=0.2)
        self.plot_co2.setLabel("left", "Concentração (ppm)", color="#94a3b8")
        self.plot_co2.setLabel("bottom", "Amostras", color="#94a3b8")
        self.plot_co2.setMinimumHeight(130)
        self.curve_co2 = self.plot_co2.plot(pen=pg.mkPen(color="#10b981", width=2))
        self.line_co2_safe = pg.InfiniteLine(pos=800, angle=0, pen=pg.mkPen(color="#eab308", width=1, style=Qt.PenStyle.DashLine))
        self.line_co2_alert = pg.InfiniteLine(pos=1200, angle=0, pen=pg.mkPen(color="#ef4444", width=1, style=Qt.PenStyle.DashLine))
        self.plot_co2.addItem(self.line_co2_safe)
        self.plot_co2.addItem(self.line_co2_alert)

        self.plot_temp = pg.PlotWidget(title="<b style='color:#f97316; font-size:12px;'>Temperatura e Ponto de Orvalho</b>")
        self.plot_temp.showGrid(x=True, y=True, alpha=0.2)
        self.plot_temp.setLabel("left", "Temperatura (°C)", color="#94a3b8")
        self.plot_temp.setLabel("bottom", "Amostras", color="#94a3b8")
        self.plot_temp.setMinimumHeight(130)
        self.plot_temp.addLegend(offset=(10, 10))
        self.curve_temp = self.plot_temp.plot(pen=pg.mkPen(color="#f97316", width=2), name="Temp (°C)")
        self.curve_dew = self.plot_temp.plot(pen=pg.mkPen(color="#38bdf8", width=1.5, style=Qt.PenStyle.DashLine), name="Orvalho (°C)")

        self.plot_hum = pg.PlotWidget(title="<b style='color:#06b6d4; font-size:12px;'>Umidade Relativa do Ar</b>")
        self.plot_hum.showGrid(x=True, y=True, alpha=0.2)
        self.plot_hum.setLabel("left", "Umidade (% RH)", color="#94a3b8")
        self.plot_hum.setLabel("bottom", "Amostras", color="#94a3b8")
        self.plot_hum.setMinimumHeight(130)
        self.curve_hum = self.plot_hum.plot(pen=pg.mkPen(color="#06b6d4", width=2))

        self.plot_press = pg.PlotWidget(title="<b style='color:#8b5cf6; font-size:12px;'>Pressão Atmosférica</b>")
        self.plot_press.showGrid(x=True, y=True, alpha=0.2)
        self.plot_press.setLabel("left", "Pressão (hPa)", color="#94a3b8")
        self.plot_press.setLabel("bottom", "Amostras", color="#94a3b8")
        self.plot_press.setMinimumHeight(130)
        self.curve_press = self.plot_press.plot(pen=pg.mkPen(color="#8b5cf6", width=2))

        grid.addWidget(self.plot_co2, 0, 0)
        grid.addWidget(self.plot_temp, 0, 1)
        grid.addWidget(self.plot_hum, 1, 0)
        grid.addWidget(self.plot_press, 1, 1)

        return container

    def create_bottom_tabs(self):
        tabs = QTabWidget()
        tabs.setMinimumHeight(260)

        tab_stats = QWidget()
        l_stats = QVBoxLayout(tab_stats)
        l_stats.setContentsMargins(6, 6, 6, 6)
        l_stats.setSpacing(4)
        self.tbl_stats = QTableWidget(6, 6)
        self.tbl_stats.setHorizontalHeaderLabels(["Grandeza", "Atual", "Média", "Mínimo", "Máximo", "Desvio Padrão"])
        self.tbl_stats.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl_stats.verticalHeader().setVisible(False)
        self.tbl_stats.verticalHeader().setDefaultSectionSize(28)
        self.tbl_stats.setMinimumHeight(210)
        l_stats.addWidget(self.tbl_stats)
        tabs.addTab(tab_stats, "📈 Estatísticas Consolidadas")

        tab_samples = QWidget()
        l_samples = QVBoxLayout(tab_samples)
        l_samples.setContentsMargins(6, 6, 6, 6)
        self.tbl_samples = QTableWidget(0, 8)
        self.tbl_samples.setHorizontalHeaderLabels([
            "Hora", "CO2 (ppm)", "Temp (°C)", "Umid (%)", "Pressão (hPa)", "Altitude (m)", "Orvalho (°C)", "Heap (KB)"
        ])
        self.tbl_samples.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl_samples.verticalHeader().setVisible(False)
        self.tbl_samples.verticalHeader().setDefaultSectionSize(26)
        l_samples.addWidget(self.tbl_samples)
        tabs.addTab(tab_samples, "📋 Tabela de Dados Históricos")

        tab_console = QWidget()
        l_console = QVBoxLayout(tab_console)
        l_console.setContentsMargins(6, 6, 6, 6)
        self.txt_console = QPlainTextEdit()
        self.txt_console.setReadOnly(True)
        self.txt_console.setMaximumBlockCount(1000)
        l_console.addWidget(self.txt_console)
        tabs.addTab(tab_console, "💻 Console Serial Nativo")

        return tabs

    def refresh_serial_ports(self):
        self.cb_ports.clear()
        ports = serial.tools.list_ports.comports()
        detected_com9_idx = 0

        for idx, p in enumerate(ports):
            desc = f"{p.device} ({p.description})"
            self.cb_ports.addItem(desc, p.device)
            if "COM9" in p.device:
                detected_com9_idx = idx

        if self.cb_ports.count() == 0:
            self.cb_ports.addItem("Nenhuma porta encontrada", "")
        else:
            self.cb_ports.setCurrentIndex(detected_com9_idx)

    def toggle_connection(self):
        if self.serial_worker and self.serial_worker.isRunning():
            self.serial_worker.stop()
            self.serial_worker = None
            self.btn_connect.setText("Conectar")
            self.btn_connect.setStyleSheet("")
            self.lbl_status.setText("Desconectado")
            self.lbl_status.setStyleSheet("background-color: #ef444422; color: #f87171; border: 1px solid #ef444455; border-radius: 4px; padding: 4px 8px; font-weight: bold; font-size: 11px;")
        else:
            port = self.cb_ports.currentData()

            if not port:
                QMessageBox.warning(self, "Aviso", "Por favor, selecione uma porta serial COM conectada ao ESP32-C5.")
                return

            baud = int(self.cb_baud.currentText())
            self.serial_worker = SerialWorker(port=port, baudrate=baud)
            self.serial_worker.data_received.connect(self.on_data_received)
            self.serial_worker.raw_line_received.connect(self.on_raw_line)
            self.serial_worker.connection_status.connect(self.on_connection_status)
            self.serial_worker.start()

            self.btn_connect.setText("Desconectar")
            self.btn_connect.setStyleSheet("background-color: #ef4444; border-color: #dc2626;")

    def on_connection_status(self, connected, msg):
        if connected:
            self.lbl_status.setText(msg)
            self.lbl_status.setStyleSheet("background-color: #10b98122; color: #4ade80; border: 1px solid #10b98155; border-radius: 4px; padding: 4px 8px; font-weight: bold; font-size: 11px;")
        else:
            self.lbl_status.setText(msg)
            self.lbl_status.setStyleSheet("background-color: #ef444422; color: #f87171; border: 1px solid #ef444455; border-radius: 4px; padding: 4px 8px; font-weight: bold; font-size: 11px;")
            self.btn_connect.setText("Conectar")
            self.btn_connect.setStyleSheet("")

    def on_raw_line(self, line):
        self.txt_console.appendPlainText(line)

    def on_data_received(self, sample):
        if not self.is_recording:
            return

        self.history.append(sample)

        row = self.tbl_samples.rowCount()
        if row >= 100:
            self.tbl_samples.removeRow(0)
            row = 99
        self.tbl_samples.insertRow(row)

        co2_val = str(sample.get("co2_ppm", "--"))
        if sample.get("co2_warmup", False):
            co2_val += f" (Warmup {sample.get('co2_warmup_rem_s', 0)}s)"

        items = [
            sample.get("timestamp", "").split()[-1],
            co2_val,
            f"{sample.get('temp_c', 0):.2f}",
            f"{sample.get('hum_pct', 0):.2f}",
            f"{sample.get('press_hpa', 0):.2f}",
            f"{sample.get('alt_m', 0):.1f}",
            f"{sample.get('dew_c', 0):.2f}",
            f"{int(sample.get('heap_free', 0) / 1024)}"
        ]
        for col, val in enumerate(items):
            item = QTableWidgetItem(val)
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tbl_samples.setItem(row, col, item)

    def update_plots_and_kpis(self):
        if not self.history:
            return

        df = pd.DataFrame(list(self.history))
        latest = self.history[-1]

        if "co2_ppm" in df.columns:
            co2_cur = latest.get("co2_ppm", 0)
            badge_text = "EXCELENTE"
            badge_color = "#10b981"
            if co2_cur >= 1500:
                badge_text = "CRÍTICO"
                badge_color = "#ef4444"
            elif co2_cur >= 1000:
                badge_text = "MODERADO"
                badge_color = "#f97316"
            elif co2_cur >= 700:
                badge_text = "BOM"
                badge_color = "#eab308"

            if latest.get("co2_warmup", False):
                badge_text = f"AQUECENDO ({latest.get('co2_warmup_rem_s', 0)}s)"
                badge_color = "#38bdf8"

            self.card_co2.lbl_badge.setStyleSheet(f"background-color: {badge_color}22; color: {badge_color}; border-radius: 4px; padding: 2px 6px; font-size: 10px; font-weight: bold;")
            self.card_co2.update_value(
                co2_cur,
                cur_str=str(co2_cur),
                badge=badge_text,
                min_v=df["co2_ppm"].min(),
                avg_v=df["co2_ppm"].mean(),
                max_v=df["co2_ppm"].max()
            )

        if "temp_c" in df.columns:
            temp_cur = latest.get("temp_c", 0.0)
            self.card_temp.update_value(
                temp_cur,
                cur_str=f"{temp_cur:.1f}",
                badge=f"Orvalho: {latest.get('dew_c', 0.0):.1f}°C",
                min_v=df["temp_c"].min(),
                avg_v=df["temp_c"].mean(),
                max_v=df["temp_c"].max()
            )

        if "hum_pct" in df.columns:
            hum_cur = latest.get("hum_pct", 0.0)
            hum_badge = "Conforto" if 40 <= hum_cur <= 70 else "Atenção"
            self.card_hum.update_value(
                hum_cur,
                cur_str=f"{hum_cur:.1f}",
                badge=hum_badge,
                min_v=df["hum_pct"].min(),
                avg_v=df["hum_pct"].mean(),
                max_v=df["hum_pct"].max()
            )

        if "press_hpa" in df.columns:
            press_cur = latest.get("press_hpa", 0.0)
            self.card_press.update_value(
                press_cur,
                cur_str=f"{press_cur:.1f}",
                badge=f"Alt: {latest.get('alt_m', 0.0):.0f}m",
                min_v=df["press_hpa"].min(),
                avg_v=df["press_hpa"].mean(),
                max_v=df["press_hpa"].max()
            )

        uptime = latest.get("uptime_s", 0)
        u_min = (uptime // 60) % 60
        u_hr = uptime // 3600
        heap_kb = int(latest.get("heap_free", 0) / 1024)
        self.card_sys.lbl_value.setText(f"{u_hr:02d}:{u_min:02d}h")
        self.card_sys.lbl_badge.setText(f"{heap_kb} KB Heap")
        self.card_sys.lbl_stats.setText(f"Amostras: {len(self.history)} | SoC: RISC-V 240MHz")

        sub_df = df.tail(150)
        x_indices = np.arange(len(sub_df))

        if "co2_ppm" in sub_df.columns:
            self.curve_co2.setData(x_indices, sub_df["co2_ppm"].values)

        if "temp_c" in sub_df.columns:
            self.curve_temp.setData(x_indices, sub_df["temp_c"].values)
            if "dew_c" in sub_df.columns:
                self.curve_dew.setData(x_indices, sub_df["dew_c"].values)

        if "hum_pct" in sub_df.columns:
            self.curve_hum.setData(x_indices, sub_df["hum_pct"].values)

        if "press_hpa" in sub_df.columns:
            self.curve_press.setData(x_indices, sub_df["press_hpa"].values)

        metrics = [
            ("CO2 NDIR (ppm)", "co2_ppm", 0),
            ("Temperatura (°C)", "temp_c", 2),
            ("Umidade Relativa (%)", "hum_pct", 2),
            ("Pressão Atmosférica (hPa)", "press_hpa", 2),
            ("Altitude Barométrica (m)", "alt_m", 1),
            ("Ponto de Orvalho (°C)", "dew_c", 2)
        ]

        for row_idx, (name, col, dec) in enumerate(metrics):
            if col in df.columns:
                series = df[col]
                cur = series.iloc[-1]
                mean_v = series.mean()
                min_v = series.min()
                max_v = series.max()
                std_v = series.std()

                vals = [
                    name,
                    f"{cur:.{dec}f}",
                    f"{mean_v:.{dec}f}",
                    f"{min_v:.{dec}f}",
                    f"{max_v:.{dec}f}",
                    f"{std_v:.{dec}f}" if not pd.isna(std_v) else "0.0"
                ]
                for col_idx, text in enumerate(vals):
                    item = QTableWidgetItem(text)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.tbl_stats.setItem(row_idx, col_idx, item)

    def clear_history(self):
        confirm = QMessageBox.question(
            self, "Confirmar Limpeza",
            "Deseja realmente limpar todos os dados coletados nesta sessão?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self.history.clear()
            self.tbl_samples.setRowCount(0)
            self.txt_console.clear()
            self.curve_co2.clear()
            self.curve_temp.clear()
            self.curve_dew.clear()
            self.curve_hum.clear()
            self.curve_press.clear()

    def export_data(self, fmt):
        if not self.history:
            QMessageBox.warning(self, "Aviso", "Nenhum dado registrado para exportação.")
            return

        df = pd.DataFrame(list(self.history))
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")

        if fmt == "csv":
            path, _ = QFileDialog.getSaveFileName(
                self, "Exportar Dados em CSV",
                f"telemetria_esp32c5_{timestamp_str}.csv",
                "Arquivos CSV (*.csv)"
            )
            if path:
                df.to_csv(path, index=False, sep=";", encoding="utf-8-sig")
                QMessageBox.information(self, "Sucesso", f"Dados exportados com sucesso em:\n{path}")

        elif fmt == "excel":
            path, _ = QFileDialog.getSaveFileName(
                self, "Exportar Dados em Excel",
                f"telemetria_esp32c5_{timestamp_str}.xlsx",
                "Planilhas Excel (*.xlsx)"
            )
            if path:
                df.to_excel(path, index=False, engine="openpyxl")
                QMessageBox.information(self, "Sucesso", f"Planilha Excel salva com sucesso em:\n{path}")

        elif fmt == "json":
            path, _ = QFileDialog.getSaveFileName(
                self, "Exportar Dados em JSON",
                f"telemetria_esp32c5_{timestamp_str}.json",
                "Arquivos JSON (*.json)"
            )
            if path:
                df.to_json(path, orient="records", indent=2)
                QMessageBox.information(self, "Sucesso", f"Arquivo JSON salvo com sucesso em:\n{path}")

    def show_about_dialog(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Sobre o Bench Monitor")
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setText("""
        <h2 style='color:#38bdf8; margin-bottom: 2px;'>Bench Monitor</h2>
        <p style='color:#94a3b8; font-size:12px; margin-top: 0px;'><b>Estação de Telemetria e Monitoramento de Bancada</b></p>
        <hr style='border: 1px solid #334155;'>
        <table style='font-size: 12px; line-height: 1.6;'>
            <tr><td><b>Autor:</b></td><td style='color:#38bdf8;'><b>Jairo Ivo Castro Brito (xToshiro)</b></td></tr>
            <tr><td><b>Licença:</b></td><td>GNU General Public License v3.0 (GPLv3)</td></tr>
            <tr><td><b>Microcontrolador:</b></td><td>Espressif ESP32-C5 (RISC-V 240 MHz)</td></tr>
            <tr><td><b>Repositório:</b></td><td><a style='color:#38bdf8; text-decoration: none;' href='https://github.com/xToshiro/bench-monitor'>https://github.com/xToshiro/bench-monitor</a></td></tr>
        </table>
        <br>
        <p style='color:#64748b; font-size:10px;'>Software livre distribuído sob os termos da licença GNU GPLv3.</p>
        """)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setStyleSheet("""
            QMessageBox {
                background-color: #0f172a;
            }
            QLabel {
                color: #e2e8f0;
                font-size: 12px;
            }
            QPushButton {
                background-color: #0284c7;
                color: white;
                font-weight: bold;
                border: 1px solid #0ea5e9;
                border-radius: 6px;
                padding: 6px 16px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #0369a1;
            }
        """)
        msg.exec()

    def closeEvent(self, event):
        if self.serial_worker and self.serial_worker.isRunning():
            self.serial_worker.stop()
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
