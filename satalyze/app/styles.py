# Satalyze: Analyze satellite images.
# Copyright (C) 2026 github.com/@bportal-sys
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# Additional Terms: Any interactive user interface utilizing this software 
# must prominently display "Powered by github.com/bportal-sys".



CARBON_SLATE_THEME_CSS = """
    :root {
        --bs-body-bg: #111318;        /* Dark Charcoal base */
        --bs-card-bg: #1a1d24;        /* Solid Slate panel background */
        --bs-border-color: #2d3139;    /* Clean, thin steel dividers */
        --bs-heading-color: #f3f4f6;
    }
    body {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        background-color: #111318 !important;
        color: #d1d5db !important;    /* Legible soft white body text */
    }
    
    /* GLOBAL TEXT FORCING (Fixes invisible sidebar and card text labels) */
    p, span, label, .control-label, .shiny-input-container {
        color: #d1d5db !important;
        font-weight: 500;
    }
    h1, h2, h3, h4, h5, h6, .card-title {
        color: #ffffff !important;
    }
    
    /* SETTINGS PAGE LABELS & DESCRIPTIONS */
    .tab-content, .nav-tabs, .container, .div {
        color: #d1d5db !important;
    }
    small, .text-muted {
        color: #9ca3af !important; /* Forces secondary info text to stay visible */
    }

    .navbar {
        background-color: #1a1d24 !important;
        border-bottom: 1px solid #2d3139 !important;
        padding: 0.75rem 1.5rem !important;
    }
    .navbar-brand {
        font-weight: 700 !important;
        color: #ffffff !important;
        letter-spacing: -0.02em;
    }
    .sidebar {
        background-color: #1a1d24 !important;
        border-right: 1px solid #2d3139 !important;
    }
       
    .sidebar-toggle, .bslib-sidebar-toggle, .btn-sidebar-toggle {
        background-color: #1a1d24 !important;
        border: 1px solid #2d3139 !important;
        color: #ffffff !important;
        opacity: 1 !important;
    }
    .sidebar-toggle:hover {
        background-color: #2d3139 !important;
    }
    
    .sidebar-toggle svg, .sidebar-toggle span, .bslib-sidebar-toggle svg, .accordion-button::after {
        filter: invert(1) brightness(2) !important; 
        color: #ffffff !important;
    }


    .card {
        background-color: #1a1d24 !important;
        border: 1px solid #2d3139 !important;
        border-radius: 6px !important;
        box-shadow: none !important;
        margin-bottom: 1rem;
    }
    .card-header {
        background-color: #1a1d24 !important;
        border-bottom: 1px solid #2d3139 !important;
        font-size: 0.85rem !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #9ca3af !important;   
        padding: 0.75rem 1rem !important;
    }

    /* FORCING TEXT VISIBILITY INSIDE WIDGET DROPDOWNS & SLIDERS */
    .form-control, .form-select, .shiny-date-input input, select, input {
        background-color: #111318 !important;
        border: 1px solid #2d3139 !important;
        color: #f3f4f6 !important; /* Explicit bright font inside inputs */
        border-radius: 4px !important;
    }
    /* Fix choices within select dropdown popovers */
    option {
        background-color: #1a1d24 !important;
        color: #f3f4f6 !important;
    }
    .form-control:focus, .form-select:focus {
        border-color: #3b82f6 !important; 
        box-shadow: 0 0 0 1px #3b82f6 !important;
    }
    
    /* COMPLETE FIX FOR INVISIBLE SHINY DATAFRAME/TABLE TEXT */
    .shiny-data-frame, .dataframe, table, th, td, 
    .table, .table td, .table th, 
    .grid-cell, .htmlwidgets-container, .table-container {
        color: #f3f4f6 !important; /* Overrides hidden black cell fonts */
        background-color: #1a1d24 !important;
        border-color: #2d3139 !important;
    }
    thead th, th {
        background-color: #111318 !important;
        color: #ffffff !important;
        font-weight: 600 !important;
    }
    .pagination, .page-link, .dataTables_info, .dataTables_length, .dataTables_filter {
        color: #9ca3af !important;
    }

    /* BUTTONS STYLE MATRIX */
    .btn-primary {
        background-color: #3b82f6 !important; 
        color: #ffffff !important;
        border: 1px solid #3b82f6 !important;
        font-weight: 600 !important;
        border-radius: 4px !important;
    }
    .btn-primary:hover {
        background-color: #2563eb !important; 
        border-color: #2563eb !important;
    }
    .btn-secondary {
        background-color: #111318 !important;
        border: 1px solid #2d3139 !important;
        color: #3b82f6 !important;            
        border-radius: 4px !important;
    }
    .btn-secondary:hover {
        background-color: #1a1d24 !important;
        border-color: #3b82f6 !important;
    }
    .btn-danger {
        background-color: #111318 !important;
        border: 1px solid #7f1d1d !important;
        color: #ef4444 !important;
        border-radius: 4px !important;
    }
    
    /* FORCE SIDEBAR TOGGLE CONTAINER AND ICON TO BE COMPLETELY VISIBLE */
    .bslib-sidebar-toggle, button.sidebar-toggle, .sidebar-toggle {
        background-color: #1a1d24 !important;
        border: 1px solid #2d3139 !important;
        opacity: 1 !important;
    }
    
    /* Invert and brighten the toggle chevron icon paths (works on SVGs and custom icons) */
    .bslib-sidebar-toggle svg, 
    button.sidebar-toggle svg, 
    .sidebar-toggle span, 
    .bslib-sidebar-toggle::after,
    [class*="sidebar-toggle"]::after {
        filter: invert(1) brightness(3) !important;
        color: #ffffff !important;
        opacity: 1 !important;
    }
    
    /* Ensure the wrapper box remains visible on the canvas boundary layout border */
    .bslib-sidebar-layout .collapse-toggle {
        overflow: visible !important;
        background-color: #1a1d24 !important;
        color: #ffffff !important;
        border-left: 1px solid #2d3139 !important;
    }
    .flatpickr-calendar, .dropdown-menu {
        z-index: 99999 !important;
    }

    #project_id::placeholder {
        color: #9ca3af !important; /* Elegant slate-gray: lighter than dark gray, dimmer than white */
        opacity: 1;                 /* Override browser default opacity fades */
        font-weight: 400;
    }
    
    .card-header .shiny-input-container {
        margin-bottom: 0 !important;
        padding-top: 0 !important;
        display: inline-block !important;
        width: auto !important;
    }
    .card-header .form-check {
        padding-top: 0 !important;
        margin-bottom: 0 !important;
    }

    .form-check-input, .shiny-input-switch input[type="checkbox"] {
        background-color: #242936 !important;
        border-color: #3b4252 !important;
        cursor: pointer;
        transition: background-color 0.15s ease-in-out, border-color 0.15s ease-in-out;
    }
    
    /* Inner circle notch tracking styling when OFF */
    .form-check-input:not(:checked) {
        background-image: url("data:image/svg+xml,%3csvg xmlns='http://w3.org' viewBox='0 0 20 20'%3e%3ccircle cx='10' cy='10' r='7' fill='%239ca3af'/%3e%3c/svg%3e") !important;
    }

    /* 2. THE "ON" STATE (Lighter Corporate Royal Blue Highlight) */
    .form-check-input:checked, .shiny-input-switch input[type="checkbox"]:checked {
        background-color: #3b82f6 !important; /* Level 1 Accent Blue */
        border-color: #3b82f6 !important;
        background-image: url("data:image/svg+xml,%3csvg xmlns='http://w3.org' viewBox='0 0 20 20'%3e%3ccircle cx='10' cy='10' r='7' fill='%23ffffff'/%3e%3c/svg%3e") !important;
    }
    
    /* Subtle glow color ring when active or focused */
    .form-check-input:focus {
        border-color: #3b82f6 !important;
        box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.25) !important;
    }

    .navbar {
    position: relative !important;
    z-index: 10002 !important;
    pointer-events: auto !important;
    }

    code {
        color: #60a5fa !important;            
        background-color: #111318 !important;
        border: 1px solid #2d3139;
        padding: 2px 6px !important;
        border-radius: 4px !important;
    }
    hr {
        border-color: #2d3139 !important;
        opacity: 1 !important;
    }
"""
