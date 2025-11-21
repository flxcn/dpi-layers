#!/usr/bin/env python3
"""
Generate an interactive map showing DPI payment systems by country with toggleable layers.
Layers include: Payment System Type, Operator, Bank Participation, Status, and more.
"""

import json
import csv
from typing import Dict, List, Tuple
from collections import defaultdict

# Country name mappings to handle variations
COUNTRY_MAPPINGS = {
    'United States': 'United States of America',
    'USA': 'United States of America',
    'UK': 'United Kingdom',
    'UAE': 'United Arab Emirates',
    'South Korea': 'Republic of Korea',
    'Korea': 'Republic of Korea',
    'Russia': 'Russian Federation',
}

def normalize_country_name(name: str) -> str:
    """Normalize country names for matching."""
    name = name.strip()
    return COUNTRY_MAPPINGS.get(name, name)

def load_payment_data(csv_file: str, filter_realtime_implemented: bool = False) -> Dict[str, List[Dict]]:
    """Load payment system data from CSV and group by country."""
    payment_by_country = defaultdict(list)

    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            country = normalize_country_name(row.get('Country / Region', ''))
            if not country or country in ['Africa', 'Asia', 'Europe']:
                continue  # Skip regional entries

            # Apply filters if requested
            if filter_realtime_implemented:
                active_realtime = row.get('Active real-time payment system present', 'No')
                status = row.get('Status of payment system implementation', 'NA')
                if active_realtime != 'Yes' or status != 'Implemented':
                    continue  # Skip non-real-time or non-implemented systems

            # Store all payment system info
            system_info = {
                'name': row.get('Payment system name', 'Unknown'),
                'payment_type': row.get('Payment system type', 'NA'),
                'operator': row.get('Operator', 'NA'),
                'bank_participation': row.get('Bank participation', 'NA'),
                'nonbank_participation': row.get('Non-bank participation', 'NA'),
                'status': row.get('Status of payment system implementation', 'NA'),
                'national_regional': row.get('National / Regional', 'National'),
                'settlement_type': row.get('Type of settlement system', 'NA'),
                'qr_code': row.get('QR code based transactions', 'NA'),
                'cross_border': row.get('Cross-border payments', 'NA'),
                'transactions_supported': row.get('Types of transactions supported', 'NA'),
                'active': row.get('Active real-time payment system present', 'No'),
                'url': row.get('URL', ''),
            }

            payment_by_country[country].append(system_info)

    return dict(payment_by_country)

def get_color_for_payment_type(payment_type: str) -> str:
    """Get color for payment system type."""
    colors = {
        'Interbank payment system': '#2E7D32',  # Dark green
        'Cross-domain payment system': '#1976D2',  # Blue
        'Mobile money': '#F57C00',  # Orange
        'CBDC': '#7B1FA2',  # Purple
        'Mobile wallet': '#C2185B',  # Pink
        'Interbank payment system, Mobile wallet': '#00796B',  # Teal
        'NA': '#9E9E9E',  # Gray
    }
    return colors.get(payment_type, '#757575')

def get_color_for_operator(operator: str) -> str:
    """Get color for operator type."""
    colors = {
        'Central bank': '#1565C0',  # Dark blue
        'Bank association': '#00897B',  # Teal
        'Commercial bank/Private PSP': '#6A1B9A',  # Purple
        'Private PSP': '#AD1457',  # Pink
        'Central bank/Bank association': '#0277BD',  # Light blue
        'Other': '#F57C00',  # Orange
        'NA': '#9E9E9E',  # Gray
    }
    return colors.get(operator.strip(), '#757575')

def get_color_for_status(status: str) -> str:
    """Get color for implementation status."""
    colors = {
        'Implemented': '#2E7D32',  # Dark green
        'Planned/Piloted': '#F9A825',  # Amber
        'NA': '#9E9E9E',  # Gray
    }
    return colors.get(status, '#757575')

def get_color_for_yes_no(value: str) -> str:
    """Get color for yes/no fields."""
    colors = {
        'Yes': '#2E7D32',  # Green
        'No': '#D32F2F',  # Red
        'NA': '#9E9E9E',  # Gray
    }
    return colors.get(value, '#757575')

def get_color_for_settlement(settlement: str) -> str:
    """Get color for settlement type."""
    colors = {
        'RTGS': '#1565C0',  # Dark blue
        'DNS': '#00897B',  # Teal
        'ACH': '#6A1B9A',  # Purple
        'MN': '#F57C00',  # Orange
        'Distributed settlement': '#00796B',  # Teal
        'NA': '#9E9E9E',  # Gray
    }
    # Handle combined types by taking the first one
    settlement_clean = settlement.split(',')[0].strip() if settlement else 'NA'
    return colors.get(settlement_clean, '#757575')

def get_color_for_national_regional(nr: str) -> str:
    """Get color for national/regional."""
    colors = {
        'National': '#1976D2',  # Blue
        'Regional': '#388E3C',  # Green
    }
    return colors.get(nr, '#757575')

def build_popup_html(country: str, systems: List[Dict]) -> str:
    """Build popup HTML for a country."""
    html = f"<b>{country}</b><br/><br/>"
    html += f"<b>Payment Systems: {len(systems)}</b><br/><br/>"

    for i, sys in enumerate(systems[:5]):  # Limit to 5 systems
        html += f"<b>{i+1}. {sys['name']}</b><br/>"
        html += f"Type: {sys['payment_type']}<br/>"
        html += f"Operator: {sys['operator']}<br/>"
        html += f"Status: {sys['status']}<br/>"
        if sys['active'] == 'Yes':
            html += f"✓ Active real-time system<br/>"
        html += "<br/>"

    if len(systems) > 5:
        html += f"<i>...and {len(systems) - 5} more systems</i><br/>"

    return html

def generate_layer_markers(payment_data: Dict[str, List[Dict]], layer_type: str) -> List[Dict]:
    """Generate markers for a specific layer."""
    markers = []

    for country, systems in payment_data.items():
        # Get the most relevant system for this country
        # For countries with multiple systems, prioritize active/implemented ones
        active_systems = [s for s in systems if s['active'] == 'Yes']
        implemented_systems = [s for s in systems if s['status'] == 'Implemented']

        primary_system = None
        if active_systems:
            primary_system = active_systems[0]
        elif implemented_systems:
            primary_system = implemented_systems[0]
        else:
            primary_system = systems[0]

        # Determine color based on layer type
        if layer_type == 'payment_type':
            color = get_color_for_payment_type(primary_system['payment_type'])
            value = primary_system['payment_type']
        elif layer_type == 'operator':
            color = get_color_for_operator(primary_system['operator'])
            value = primary_system['operator']
        elif layer_type == 'bank_participation':
            color = get_color_for_yes_no(primary_system['bank_participation'])
            value = primary_system['bank_participation']
        elif layer_type == 'nonbank_participation':
            color = get_color_for_yes_no(primary_system['nonbank_participation'])
            value = primary_system['nonbank_participation']
        elif layer_type == 'status':
            color = get_color_for_status(primary_system['status'])
            value = primary_system['status']
        elif layer_type == 'settlement_type':
            color = get_color_for_settlement(primary_system['settlement_type'])
            value = primary_system['settlement_type'].split(',')[0].strip() if primary_system['settlement_type'] else 'NA'
        elif layer_type == 'national_regional':
            color = get_color_for_national_regional(primary_system['national_regional'])
            value = primary_system['national_regional']
        elif layer_type == 'qr_code':
            color = get_color_for_yes_no(primary_system['qr_code'])
            value = primary_system['qr_code']
        else:
            color = '#757575'
            value = 'Unknown'

        popup = build_popup_html(country, systems)

        markers.append({
            'country': country,
            'color': color,
            'value': value,
            'popup': popup,
            'system_count': len(systems)
        })

    return markers

def get_legend_items(layer_type: str) -> Tuple[str, List[Tuple[str, str]]]:
    """Get legend title and items for a layer type."""
    legends = {
        'payment_type': ('Payment System Type', [
            ('#2E7D32', 'Interbank payment system'),
            ('#1976D2', 'Cross-domain payment system'),
            ('#F57C00', 'Mobile money'),
            ('#7B1FA2', 'CBDC'),
            ('#C2185B', 'Mobile wallet'),
            ('#9E9E9E', 'NA/Other'),
        ]),
        'operator': ('Operator', [
            ('#1565C0', 'Central bank'),
            ('#00897B', 'Bank association'),
            ('#6A1B9A', 'Commercial bank/Private PSP'),
            ('#AD1457', 'Private PSP'),
            ('#9E9E9E', 'NA/Other'),
        ]),
        'bank_participation': ('Bank Participation', [
            ('#2E7D32', 'Yes'),
            ('#D32F2F', 'No'),
            ('#9E9E9E', 'NA'),
        ]),
        'nonbank_participation': ('Non-Bank Participation', [
            ('#2E7D32', 'Yes'),
            ('#D32F2F', 'No'),
            ('#9E9E9E', 'NA'),
        ]),
        'status': ('Implementation Status', [
            ('#2E7D32', 'Implemented'),
            ('#F9A825', 'Planned/Piloted'),
            ('#9E9E9E', 'NA'),
        ]),
        'settlement_type': ('Settlement System Type', [
            ('#1565C0', 'RTGS'),
            ('#00897B', 'DNS'),
            ('#6A1B9A', 'ACH'),
            ('#F57C00', 'MN'),
            ('#9E9E9E', 'NA/Other'),
        ]),
        'national_regional': ('Scope', [
            ('#1976D2', 'National'),
            ('#388E3C', 'Regional'),
        ]),
        'qr_code': ('QR Code Based', [
            ('#2E7D32', 'Yes'),
            ('#D32F2F', 'No'),
            ('#9E9E9E', 'NA'),
        ]),
    }
    return legends.get(layer_type, ('Unknown', []))

def generate_html_map(payment_data: Dict[str, List[Dict]], output_file: str):
    """Generate interactive HTML map with multiple layers."""

    # Generate markers for each layer type
    layer_types = [
        'payment_type',
        'operator',
        'status',
        'bank_participation',
        'nonbank_participation',
        'settlement_type',
        'national_regional',
        'qr_code'
    ]

    layers_data = {}
    for layer_type in layer_types:
        layers_data[layer_type] = generate_layer_markers(payment_data, layer_type)

    # Get country coordinates
    country_coords = get_country_coordinates()

    # Generate HTML
    html_content = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Real-Time Payment Systems Map (Implemented)</title>

    <!-- Leaflet CSS -->
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />

    <style>
        body {
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        }
        #map {
            width: 100%;
            height: 600px;
        }
        .legend {
            background: white;
            padding: 10px;
            border-radius: 5px;
            box-shadow: 0 1px 5px rgba(0,0,0,0.4);
            line-height: 20px;
            color: #555;
            max-height: 500px;
            overflow-y: auto;
        }
        .legend h4 {
            margin: 0 0 8px;
            font-size: 13px;
            font-weight: 600;
        }
        .legend-item {
            margin-bottom: 4px;
            display: flex;
            align-items: center;
            font-size: 12px;
        }
        .legend-color {
            width: 16px;
            height: 16px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 6px;
            border: 1px solid #999;
            flex-shrink: 0;
        }
        .info {
            padding: 6px 8px;
            font: 14px/16px Arial, Helvetica, sans-serif;
            background: white;
            background: rgba(255,255,255,0.9);
            box-shadow: 0 0 15px rgba(0,0,0,0.2);
            border-radius: 5px;
        }
        .info h4 {
            margin: 0 0 5px;
            color: #777;
            font-size: 14px;
        }
        .layer-control {
            background: white;
            padding: 10px;
            border-radius: 5px;
            box-shadow: 0 1px 5px rgba(0,0,0,0.4);
            max-height: 500px;
            overflow-y: auto;
        }
        .layer-control h4 {
            margin: 0 0 8px 0;
            font-size: 13px;
            font-weight: 600;
        }
        .layer-control button {
            display: block;
            width: 100%;
            margin: 4px 0;
            padding: 6px 8px;
            border: 1px solid #ccc;
            background: #f8f9fa;
            cursor: pointer;
            border-radius: 3px;
            font-size: 12px;
            text-align: left;
        }
        .layer-control button.active {
            background: #007bff;
            color: white;
            border-color: #007bff;
            font-weight: 500;
        }
        .layer-control button:hover {
            background: #e9ecef;
        }
        .layer-control button.active:hover {
            background: #0056b3;
        }
    </style>
</head>
<body>
    <div id="map"></div>

    <!-- Leaflet JS -->
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>

    <script>
        // Initialize map
        var map = L.map('map').setView([20, 0], 2);

        // Add tile layer
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            maxZoom: 18,
        }).addTo(map);

        // Country coordinates
        var countryCoords = ''' + json.dumps(country_coords) + ''';

        // Layer data
        var layersData = ''' + json.dumps(layers_data) + ''';

        // Layer legends
        var layerLegends = ''' + json.dumps({lt: get_legend_items(lt) for lt in layer_types}) + ''';

        // Current layer
        var currentLayer = 'payment_type';
        var currentMarkers = L.layerGroup().addTo(map);

        // Function to update map with current layer
        function updateMap() {
            currentMarkers.clearLayers();

            var markers = layersData[currentLayer];
            markers.forEach(function(marker) {
                var coords = countryCoords[marker.country];
                if (coords) {
                    var circle = L.circleMarker([coords[0], coords[1]], {
                        radius: 6 + (marker.system_count > 1 ? 2 : 0),
                        fillColor: marker.color,
                        color: '#000',
                        weight: 1,
                        opacity: 1,
                        fillOpacity: 0.8
                    });
                    circle.bindPopup(marker.popup);
                    currentMarkers.addLayer(circle);
                }
            });

            updateLegend();
        }

        // Add layer control
        var layerControl = L.control({position: 'topright'});

        layerControl.onAdd = function (map) {
            var div = L.DomUtil.create('div', 'layer-control');
            div.innerHTML = '<h4>Select Layer</h4>' +
                '<button id="btn-payment_type" class="active">Payment System Type</button>' +
                '<button id="btn-operator">Operator</button>' +
                '<button id="btn-status">Implementation Status</button>' +
                '<button id="btn-bank_participation">Bank Participation</button>' +
                '<button id="btn-nonbank_participation">Non-Bank Participation</button>' +
                '<button id="btn-settlement_type">Settlement Type</button>' +
                '<button id="btn-national_regional">National/Regional</button>' +
                '<button id="btn-qr_code">QR Code Support</button>';
            return div;
        };

        layerControl.addTo(map);

        // Add legend
        var legend = L.control({position: 'bottomright'});
        var legendDiv;

        legend.onAdd = function (map) {
            legendDiv = L.DomUtil.create('div', 'legend');
            updateLegend();
            return legendDiv;
        };

        function updateLegend() {
            if (!legendDiv) return;

            var legendInfo = layerLegends[currentLayer];
            var title = legendInfo[0];
            var items = legendInfo[1];

            legendDiv.innerHTML = '<h4>' + title + '</h4>';
            items.forEach(function(item) {
                legendDiv.innerHTML += '<div class="legend-item">' +
                    '<span class="legend-color" style="background:' + item[0] + '"></span>' +
                    '<span>' + item[1] + '</span></div>';
            });
        }

        legend.addTo(map);

        // Layer switching handlers
        setTimeout(function() {
            var layerButtons = [
                'payment_type', 'operator', 'status', 'bank_participation',
                'nonbank_participation', 'settlement_type', 'national_regional', 'qr_code'
            ];

            layerButtons.forEach(function(layerType) {
                document.getElementById('btn-' + layerType).addEventListener('click', function() {
                    if (currentLayer !== layerType) {
                        // Remove active class from all buttons
                        layerButtons.forEach(function(lt) {
                            document.getElementById('btn-' + lt).classList.remove('active');
                        });

                        // Add active class to clicked button
                        this.classList.add('active');

                        // Update current layer and refresh map
                        currentLayer = layerType;
                        updateMap();
                    }
                });
            });
        }, 100);

        // Add info box
        var info = L.control({position: 'topleft'});

        info.onAdd = function (map) {
            this._div = L.DomUtil.create('div', 'info');
            this._div.innerHTML = '<h4>Real-Time Payment Systems (Implemented)</h4>' +
                '<p>Click markers for details. Switch layers to explore different attributes.</p>';
            return this._div;
        };

        info.addTo(map);

        // Initial map render
        updateMap();
    </script>
</body>
</html>'''

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"Map generated successfully: {output_file}")
    print(f"Total countries mapped: {len(payment_data)}")
    print(f"Total payment systems: {sum(len(systems) for systems in payment_data.values())}")

def get_country_coordinates() -> Dict[str, List[float]]:
    """Return approximate country coordinates (lat, lon)."""
    return {
        # Major countries - approximate centroids
        "Afghanistan": [33.0, 65.0],
        "Albania": [41.0, 20.0],
        "Algeria": [28.0, 3.0],
        "Andorra": [42.5, 1.5],
        "Angola": [-12.5, 18.5],
        "Antigua and Barbuda": [17.05, -61.8],
        "Argentina": [-34.0, -64.0],
        "Armenia": [40.0, 45.0],
        "Australia": [-25.0, 135.0],
        "Austria": [47.5, 14.5],
        "Azerbaijan": [40.5, 47.5],
        "Bahamas": [24.25, -76.0],
        "Bahrain": [26.0, 50.5],
        "Bangladesh": [24.0, 90.0],
        "Barbados": [13.2, -59.5],
        "Belarus": [53.0, 28.0],
        "Belgium": [50.8, 4.0],
        "Belize": [17.25, -88.75],
        "Benin": [9.5, 2.25],
        "Bhutan": [27.5, 90.5],
        "Bolivia": [-17.0, -65.0],
        "Bosnia and Herzegovina": [44.0, 18.0],
        "Botswana": [-22.0, 24.0],
        "Brazil": [-10.0, -55.0],
        "Brunei": [4.5, 114.67],
        "Bulgaria": [43.0, 25.0],
        "Burkina Faso": [13.0, -2.0],
        "Burundi": [-3.5, 30.0],
        "Cabo Verde": [16.0, -24.0],
        "Cambodia": [13.0, 105.0],
        "Cameroon": [6.0, 12.0],
        "Canada": [60.0, -95.0],
        "Central African Republic": [7.0, 21.0],
        "Chad": [15.0, 19.0],
        "Chile": [-30.0, -71.0],
        "China": [35.0, 105.0],
        "Colombia": [4.0, -72.0],
        "Comoros": [-12.17, 44.25],
        "Congo": [-1.0, 15.0],
        "Costa Rica": [10.0, -84.0],
        "Croatia": [45.1, 15.2],
        "Cuba": [21.5, -80.0],
        "Cyprus": [35.0, 33.0],
        "Czechia": [49.75, 15.5],
        "Denmark": [56.0, 10.0],
        "Djibouti": [11.5, 43.0],
        "Dominica": [15.42, -61.33],
        "Dominican Republic": [19.0, -70.5],
        "Ecuador": [-2.0, -77.5],
        "Egypt": [27.0, 30.0],
        "El Salvador": [13.8, -88.9],
        "Equatorial Guinea": [2.0, 10.0],
        "Estonia": [59.0, 26.0],
        "Eswatini": [-26.5, 31.5],
        "Ethiopia": [8.0, 38.0],
        "Fiji": [-18.0, 175.0],
        "Finland": [64.0, 26.0],
        "France": [46.0, 2.0],
        "Gabon": [-1.0, 11.75],
        "Gambia": [13.5, -15.5],
        "Georgia": [42.0, 43.5],
        "Germany": [51.0, 9.0],
        "Ghana": [8.0, -2.0],
        "Greece": [39.0, 22.0],
        "Grenada": [12.12, -61.67],
        "Guatemala": [15.5, -90.25],
        "Guinea": [11.0, -10.0],
        "Guinea-Bissau": [12.0, -15.0],
        "Guyana": [5.0, -59.0],
        "Haiti": [19.0, -72.42],
        "Honduras": [15.0, -86.5],
        "Hong Kong": [22.3, 114.2],
        "Hungary": [47.0, 20.0],
        "Iceland": [65.0, -18.0],
        "India": [20.0, 77.0],
        "Indonesia": [-5.0, 120.0],
        "Iran": [32.0, 53.0],
        "Iraq": [33.0, 44.0],
        "Ireland": [53.0, -8.0],
        "Israel": [31.5, 34.75],
        "Italy": [42.8, 12.8],
        "Jamaica": [18.25, -77.5],
        "Japan": [36.0, 138.0],
        "Jordan": [31.0, 36.0],
        "Kazakhstan": [48.0, 68.0],
        "Kenya": [1.0, 38.0],
        "Kiribati": [1.42, 173.0],
        "Kosovo": [42.67, 21.17],
        "Kuwait": [29.5, 45.75],
        "Kyrgyzstan": [41.0, 75.0],
        "Laos": [18.0, 105.0],
        "Latvia": [57.0, 25.0],
        "Lebanon": [33.8, 35.8],
        "Lesotho": [-29.5, 28.5],
        "Liberia": [6.5, -9.5],
        "Libya": [25.0, 17.0],
        "Liechtenstein": [47.17, 9.53],
        "Lithuania": [56.0, 24.0],
        "Luxembourg": [49.75, 6.17],
        "Macao": [22.17, 113.55],
        "Madagascar": [-20.0, 47.0],
        "Malawi": [-13.5, 34.0],
        "Malaysia": [2.5, 112.5],
        "Maldives": [3.25, 73.0],
        "Mali": [17.0, -4.0],
        "Malta": [35.9, 14.4],
        "Marshall Islands": [9.0, 168.0],
        "Mauritania": [20.0, -12.0],
        "Mauritius": [-20.3, 57.6],
        "Mexico": [23.0, -102.0],
        "Micronesia": [6.92, 158.25],
        "Moldova": [47.0, 29.0],
        "Monaco": [43.73, 7.42],
        "Mongolia": [46.0, 105.0],
        "Montenegro": [42.5, 19.3],
        "Morocco": [32.0, -5.0],
        "Mozambique": [-18.25, 35.0],
        "Myanmar": [22.0, 98.0],
        "Namibia": [-22.0, 17.0],
        "Nauru": [-0.53, 166.92],
        "Nepal": [28.0, 84.0],
        "Netherlands": [52.5, 5.75],
        "New Zealand": [-41.0, 174.0],
        "Nicaragua": [13.0, -85.0],
        "Niger": [16.0, 8.0],
        "Nigeria": [10.0, 8.0],
        "North Macedonia": [41.83, 22.0],
        "Norway": [62.0, 10.0],
        "Oman": [21.0, 57.0],
        "Pakistan": [30.0, 70.0],
        "Palau": [7.5, 134.5],
        "Palestine": [32.0, 35.25],
        "Panama": [9.0, -80.0],
        "Papua New Guinea": [-6.0, 147.0],
        "Paraguay": [-23.0, -58.0],
        "Peru": [-10.0, -76.0],
        "Philippines": [13.0, 122.0],
        "Poland": [52.0, 20.0],
        "Portugal": [39.5, -8.0],
        "Qatar": [25.5, 51.25],
        "Republic of Korea": [37.0, 127.5],
        "Romania": [46.0, 25.0],
        "Russian Federation": [60.0, 100.0],
        "Rwanda": [-2.0, 30.0],
        "Saint Kitts and Nevis": [17.33, -62.75],
        "Saint Lucia": [14.0, -61.0],
        "Saint Vincent and the Grenadines": [13.25, -61.2],
        "Samoa": [-13.58, -172.33],
        "San Marino": [43.77, 12.42],
        "Sao Tome and Principe": [1.0, 7.0],
        "Saudi Arabia": [25.0, 45.0],
        "Senegal": [14.0, -14.0],
        "Serbia": [44.0, 21.0],
        "Seychelles": [-4.58, 55.67],
        "Sierra Leone": [8.5, -11.5],
        "Singapore": [1.3, 103.8],
        "Slovakia": [48.7, 19.5],
        "Slovenia": [46.1, 14.8],
        "Solomon Islands": [-8.0, 159.0],
        "Somalia": [10.0, 49.0],
        "South Africa": [-29.0, 24.0],
        "South Sudan": [7.0, 30.0],
        "Spain": [40.0, -4.0],
        "Sri Lanka": [7.0, 81.0],
        "Sudan": [15.0, 30.0],
        "Suriname": [4.0, -56.0],
        "Sweden": [62.0, 15.0],
        "Switzerland": [47.0, 8.0],
        "Syria": [35.0, 38.0],
        "Taiwan": [23.5, 121.0],
        "Tajikistan": [39.0, 71.0],
        "Tanzania": [-6.0, 35.0],
        "Thailand": [15.0, 100.0],
        "Timor-Leste": [-8.83, 125.92],
        "Togo": [8.0, 1.17],
        "Tonga": [-20.0, -175.0],
        "Trinidad and Tobago": [11.0, -61.0],
        "Tunisia": [34.0, 9.0],
        "Turkey": [39.0, 35.0],
        "Turkmenistan": [40.0, 60.0],
        "Tuvalu": [-8.0, 178.0],
        "Uganda": [1.0, 32.0],
        "Ukraine": [49.0, 32.0],
        "United Arab Emirates": [24.0, 54.0],
        "United Kingdom": [54.0, -2.0],
        "United States of America": [38.0, -97.0],
        "Uruguay": [-33.0, -56.0],
        "Uzbekistan": [41.0, 64.0],
        "Vanuatu": [-16.0, 167.0],
        "Venezuela": [8.0, -66.0],
        "Vietnam": [16.0, 106.0],
        "Yemen": [15.0, 48.0],
        "Zambia": [-15.0, 30.0],
        "Zimbabwe": [-20.0, 30.0],
    }

if __name__ == '__main__':
    print("Processing DPI payment systems data...")
    print("Filtering: Active real-time payment systems that are implemented\n")

    # Load data with filter for real-time implemented systems only
    payment_data = load_payment_data('dpi-payments.csv', filter_realtime_implemented=True)

    print(f"Loaded {len(payment_data)} countries with real-time implemented systems")
    print(f"Total payment systems: {sum(len(systems) for systems in payment_data.values())}")

    # Generate map
    generate_html_map(payment_data, 'index.html')

    print("\nGenerated interactive map with 8 toggleable layers:")
    print("  1. Payment System Type")
    print("  2. Operator")
    print("  3. Implementation Status")
    print("  4. Bank Participation")
    print("  5. Non-Bank Participation")
    print("  6. Settlement Type")
    print("  7. National/Regional")
    print("  8. QR Code Support")
    print("\nFiltered to show only: Active real-time payment systems with 'Implemented' status")
    print("Open dpi_payments_map.html in a browser to view the map.")
