# -*- coding: utf-8 -*-
"""
/***************************************************************************
 PreAndPostFireTiffGenerator
                                 A QGIS plugin
 This Plugin creates a Pre and Post Fire Tiff file depending on the client input
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2025-03-20
        copyright            : (C) 2025 by Diego - Fire2A
        email                : diego@fire2a.com
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load PreAndPostFireTiffGenerator class from file PreAndPostFireTiffGenerator.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .tiff_generator import PreAndPostFireTiffGenerator
    return PreAndPostFireTiffGenerator(iface)
