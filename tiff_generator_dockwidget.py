import os
from qgis.PyQt import QtWidgets, uic
from qgis.PyQt.QtCore import pyqtSignal, QDate, Qt
from qgis.core import QgsProject, QgsVectorLayer, QgsFeature, QgsGeometry, QgsPointXY
from qgis.gui import QgsMapToolEmitPoint
import ee

# Cargar la UI generada con Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'tiff_generator_dockwidget_base.ui'))

class FireIgnitionTool(QgsMapToolEmitPoint):
    def __init__(self, iface, callback):
        super().__init__(iface.mapCanvas())
        self.iface = iface
        self.canvas = iface.mapCanvas()
        self.callback = callback
        self.setCursor(Qt.CrossCursor)
        print("🔥 FireIgnitionTool activado. Haz clic en el mapa para seleccionar el punto de ignición.")

    def canvasReleaseEvent(self, event):
        point = self.toMapCoordinates(event.pos())
        if point:
            print(f"📍 Punto de ignición seleccionado: {point.x()}, {point.y()}")
            self.callback(point)
            self.canvas.unsetMapTool(self)
            print("🔄 Herramienta desactivada después de la selección.")
        else:
            print("⚠️ No se pudo obtener un punto de ignición.")

class PreAndPostFireTiffGeneratorDockWidget(QtWidgets.QDockWidget, FORM_CLASS):
    closingPlugin = pyqtSignal()

    def __init__(self, iface, parent=None):
        super(PreAndPostFireTiffGeneratorDockWidget, self).__init__(parent)
        self.iface = iface
        self.setupUi(self)

        # UI Setup
        self.setWindowTitle("Generador de TIFF de Incendios")
        layout = QtWidgets.QVBoxLayout()

        # Punto de ignición
        self.label_point = QtWidgets.QLabel("Punto de ignición: No seleccionado")
        self.btn_select_point = QtWidgets.QPushButton("Seleccionar punto en el mapa")
        self.btn_select_point.clicked.connect(self.select_point)

        # Fechas
        self.label_start_date = QtWidgets.QLabel("Fecha de inicio:")
        self.start_date = QtWidgets.QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate())

        self.label_end_date = QtWidgets.QLabel("Fecha de término:")
        self.end_date = QtWidgets.QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())

        # Área o longitud del recuadro
        self.label_area = QtWidgets.QLabel("Área estimada del incendio (ha) o longitud del recuadro (m):")
        self.area_input = QtWidgets.QDoubleSpinBox()
        self.area_input.setRange(0, 10000)
        self.area_input.setSuffix(" ha")

        # Botón para generar el TIFF
        self.btn_generate = QtWidgets.QPushButton("Generar TIFF")
        self.btn_generate.clicked.connect(self.generate_tiff)

        # Agregar widgets al layout
        layout.addWidget(self.label_point)
        layout.addWidget(self.btn_select_point)
        layout.addWidget(self.label_start_date)
        layout.addWidget(self.start_date)
        layout.addWidget(self.label_end_date)
        layout.addWidget(self.end_date)
        layout.addWidget(self.label_area)
        layout.addWidget(self.area_input)
        layout.addWidget(self.btn_generate)

        container = QtWidgets.QWidget()
        container.setLayout(layout)
        self.setWidget(container)

        self.ignition_point = None
        self.ee_initialize()

    def ee_initialize(self):
        try:
            ee.Initialize()
        except Exception as e:
            print(f"Error al inicializar Google Earth Engine: {e}")

    def select_point(self):
        print("🛠 Activando herramienta de selección de punto de ignición...")
        self.tool = FireIgnitionTool(self.iface, self.set_point)
        self.iface.mapCanvas().setMapTool(self.tool)
        self.iface.mapCanvas().refresh()

    def set_point(self, point):
        if point:
            self.ignition_point = point
            self.label_point.setText(f"Punto de ignición: {point.x()}, {point.y()}")
            print(f"✅ Punto de ignición confirmado: {point.x()}, {point.y()}")
        else:
            print("⚠️ Error: No se capturó un punto válido.")

    def generate_tiff(self):
        if not self.ignition_point:
            print("⚠️ No se ha seleccionado un punto de ignición.")
            self.label_point.setText("Selecciona un punto de ignición primero")
            return

        start_date = self.start_date.date().toString("yyyy-MM-dd")
        end_date = self.end_date.date().toString("yyyy-MM-dd")
        buffer_distance = self.area_input.value() * 100
        print("🚀 Iniciando generación de imágenes pre y post incendio...")

        self.get_fire_images(start_date, end_date, buffer_distance)

    def get_fire_images(self, start_date, end_date, buffer_distance):
        region = ee.Geometry.Point([self.ignition_point.x(), self.ignition_point.y()]).buffer(buffer_distance)
        
        # Cargar imágenes Landsat 5, 7, 8 y 9
        sat = (ee.ImageCollection('LANDSAT/LT05/C02/T1_L2')
               .merge(ee.ImageCollection('LANDSAT/LE07/C02/T1_L2'))
               .merge(ee.ImageCollection('LANDSAT/LC08/C02/T1_L2'))
               .merge(ee.ImageCollection('LANDSAT/LC09/C02/T1_L2'))
               .filterBounds(region))
        
        # Definir mosaicos pre y post-incendio
        mosaicpre = sat.filterDate(ee.Date(start_date).advance(-365, 'day'), ee.Date(start_date)).mosaic().clip(region)
        mosaicpos = sat.filterDate(ee.Date(end_date), ee.Date(end_date).advance(180, 'day')).mosaic().clip(region)
        
        # Guardar imágenes localmente
        pre_path = os.path.join(os.path.dirname(__file__), f"ImgPreF_{start_date}.tif")
        post_path = os.path.join(os.path.dirname(__file__), f"ImgPosF_{end_date}.tif")

        print(f"💾 Guardando imágenes en: {pre_path} y {post_path}")
        
        ee.batch.Export.image.toDrive(
            image=mosaicpre,
            description=f'ImgPreF_{start_date}',
            folder=pre_path,
            scale=30,
            region=region.getInfo()['coordinates'],
            maxPixels=1e13,
            fileFormat='GeoTIFF'
        ).start()
        
        ee.batch.Export.image.toDrive(
            image=mosaicpos,
            description=f'ImgPosF_{end_date}',
            folder=post_path,
            scale=30,
            region=region.getInfo()['coordinates'],
            maxPixels=1e13,
            fileFormat='GeoTIFF'
        ).start()
        
        print(f"🚀 Exportación completada. Archivos guardados en: {pre_path} y {post_path}")