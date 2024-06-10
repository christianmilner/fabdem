# -*- coding: utf-8 -*-
"""
/***************************************************************************
 _fabdem
                                 A QGIS plugin
 FABDEM-tile-finder
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2024-06-09
        git sha              : $Format:%H$
        copyright            : (C) 2024 by Christian Milner / SLR
        email                : cmilner@slrconsulting.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QFileDialog, QDialog, QApplication, QDialogButtonBox
from qgis.core import QgsProject, Qgis, QgsMapLayer, QgsWkbTypes, QgsMapLayerProxyModel, QgsRasterLayer
from PyQt5.QtGui import QIcon
from qgis.gui import QgsMapLayerComboBox

# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .fabdem_dialog import _fabdemDialog
import os.path
from pathlib import Path
from shapely.geometry import box, mapping
import geopandas as gpd
import rasterio
import rioxarray
import fiona
import concurrent.futures


class _fabdem:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            '_fabdem_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&FABDEM')
        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('_fabdem', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/fabdem/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'FABDEM-tile-finder'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True

    # Custom functions here:

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&FABDEM'),
                action)
            self.iface.removeToolBarIcon(action)

    def updateOkButtonState(self):
        # Enable the "OK" button if the line edit is not empty; otherwise, disable it
        fabdem_folder = self.dlg.tileLineEdit.text()
        ok_button = self.dlg.buttonBox.button(QDialogButtonBox.Ok)
        ok_button.setEnabled(bool(fabdem_folder))

    def selectFabdemTiles(self) -> str:
        filename = QFileDialog.getExistingDirectory(
            self.dlg, "Select FABDEM tiles", "/",)
        self.dlg.tileLineEdit.setText(filename)
        self.dlg.progressBar.setValue(0)

    def getTiles(self, folder_path) -> list:
        try:
            path = Path(folder_path)
            tiles = [str(tile) for tile in path.rglob('*.tif')]
            return tiles
        except Exception as e:
            self.iface.messageBar().pushMessage(f"Error in getTiles {e}", level=Qgis.Warning, duration=3)
            print("Error in getTiles:", e)
            return []
        
    def getTileBounds(self, tile: str, shp_crs: str) -> list:
        with rioxarray.open_rasterio(tile) as tile:
            return box(*tile.rio.transform_bounds(shp_crs))
        
    def getShapefile(self, shapefile: str) -> tuple:
        shp = gpd.read_file(shapefile)
        return shp.total_bounds, shp.crs, shp.geometry
    
    def checkTileIntersection(self, shapefile_bounds:list, tile_bounds: list) -> bool:
        shp_bbox = box(*shapefile_bounds)
        return shp_bbox.intersects(tile_bounds)

    # def clipTile(self, tile: str, shp_crs: str, shp_geometry: gpd.GeoSeries) -> None:
    #     with rioxarray.open_rasterio(tile) as tile_ds:
    #         repro_tile = tile_ds.rio.reproject(shp_crs)
    #         clipped_tile = repro_tile.rio.clip(shp_geometry, drop=True)
    #         if args.filename is not None:
    #             clipped_tile.rio.to_raster(args.filename)
    #             logging.info(f' Saving clipped tile to {args.filename}')
    #         else:
    #             filename = f'Clipped_{os.path.basename(tile)}'
    #             clipped_tile.rio.to_raster(filename)
    #             logging.info(f' Saving clipped tile to {filename}')

    def processTile(self, tile: str, shp_crs: str, shp_bounds: list) -> str | None:
        try:
            tile_bounds = self.getTileBounds(tile, shp_crs)
            if self.checkTileIntersection(shp_bounds, tile_bounds):
                return tile
        except Exception as e:
            print(f"Error processing {tile}: {e}")
        return None
    
    def updateProgressBar(self, value, total):
        if total > 0:
            percentage = int((value / total) * 100)
            self.dlg.progressBar.setValue(percentage)


    def onAccepted(self):
        # Actions to perform when the user clicks "OK"
        fabdem_folder = self.dlg.tileLineEdit.text()

        fabdem_tiles = self.getTiles(fabdem_folder)

        if fabdem_tiles:
            self.iface.messageBar().pushMessage(f'Found {len(fabdem_tiles)} tiles in {fabdem_folder}', level=Qgis.Success, duration=1)
            print("Found tiles:", len(fabdem_tiles))
        else:
            self.iface.messageBar().pushMessage("No tiles found in selected folder", level=Qgis.Warning, duration=3)
            print("No tiles found in the selected folder.")

        shapefile_layer = self.dlg.extentMapLayerComboBox.currentLayer()

        if not shapefile_layer:
            self.iface.messageBar().pushMessage("No Layer selected", level=Qgis.Warning, duration=3)
            return
        
        self.iface.messageBar().pushMessage(f"Layer Selected: {shapefile_layer.name()}", level=Qgis.Success, duration=3)

        shp_bounds, shp_crs, shp_geometry = self.getShapefile(shapefile_layer.source())

        intersecting_tiles = []

        # Set up progress bar
        total_tiles = len(fabdem_tiles)
        self.dlg.progressBar.setRange(0, total_tiles)
        self.updateProgressBar(0, total_tiles)

        # Iterate over each tile
        for i, tile in enumerate(fabdem_tiles):
            # Update progress bar
            self.updateProgressBar(i + 1, total_tiles)

            processed_tile = self.processTile(tile, shp_crs, shp_bounds)
            if processed_tile is not None:
                intersecting_tiles.append(processed_tile)

        if intersecting_tiles:
            # Add intersecting tiles as raster layers to the QGIS project
            for tile_path in intersecting_tiles:
                tile_layer = QgsRasterLayer(tile_path, os.path.basename(tile_path), "gdal")
                if tile_layer.isValid():
                    QgsProject.instance().addMapLayer(tile_layer)
                else:
                    self.iface.messageBar().pushMessage(f"Failed to load tile layer: {tile_path}, {tile_layer.error().summary()}", level=Qgis.Warning, duration=3)

        # Reset dialog
        self.resetDialogState()
        self.dlg.accept()

    def onRejected(self):
        # Actions to perform when the user clicks "Cancel"
        self.dlg.reject()

    
    def resetDialogState(self):
        # Clear fabdem tiles
        self.dlg.tileLineEdit.clear()    

        # Disable the "OK" button
        ok_button = self.dlg.buttonBox.button(QDialogButtonBox.Ok)
        ok_button.setEnabled(False)

        # # Clear any messages displayed in the message bar
        # self.iface.messageBar().clearWidgets()


    def run(self):
        """Run method that performs all the real work"""

        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if self.first_start == True:
            self.first_start = False
            self.dlg = _fabdemDialog(parent=self.iface.mainWindow())

            # Set window flag to stay on top
            self.dlg.setWindowFlag(Qt.WindowStaysOnTopHint)

            # Disable the "OK" button initially
            ok_button = self.dlg.buttonBox.button(QDialogButtonBox.Ok)
            ok_button.setEnabled(False)

            # Connect line edit's textChanged signal to updateOkButtonState method
            self.dlg.tileLineEdit.textChanged.connect(self.updateOkButtonState)

            # Populate extendComboBox with vector layer names
            self.dlg.extentMapLayerComboBox.setShowCrs(True)
            self.dlg.extentMapLayerComboBox.setFilters(QgsMapLayerProxyModel.PolygonLayer)

            # Connect button method for selecting FABDEM folder
            self.dlg.tilePushButton.clicked.connect(self.selectFabdemTiles)

            # Connect button method for 'Ok' and 'Cancel' buttons
            self.dlg.buttonBox.accepted.connect(self.onAccepted)
            self.dlg.buttonBox.rejected.connect(self.onRejected)

            # Set progress bar to 0
            self.dlg.progressBar.setValue(0)
        

        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()