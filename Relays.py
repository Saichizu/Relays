#!/usr/bin/env python3
"""
Relays - Table Management System with Timer Controls
A NiceGUI application for managing pool tables with timer functionality.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional
from nicegui import ui, app

# Global state tracking
tables: Dict[int, Dict] = {}

# CSS Styles
CUSTOM_CSS = """
<style>
.hidden {
    display: none !important;
}

.table-card {
    border: 2px solid #e0e0e0;
    border-radius: 8px;
    padding: 16px;
    margin: 8px;
    background: white;
}

.table-header {
    font-size: 20px;
    font-weight: bold;
    margin-bottom: 12px;
    color: #333;
}

.timer-display {
    font-size: 24px;
    font-weight: bold;
    color: #2196F3;
    margin: 12px 0;
}

.status-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 4px;
    font-size: 14px;
    font-weight: 500;
    margin-bottom: 12px;
}

.status-idle {
    background-color: #e8f5e9;
    color: #2e7d32;
}

.status-active {
    background-color: #fff3e0;
    color: #e65100;
}

.status-open {
    background-color: #e3f2fd;
    color: #1565c0;
}

.status-expired {
    background-color: #ffebee;
    color: #c62828;
}

.button-row {
    display: flex;
    gap: 8px;
    margin-top: 12px;
}
</style>
"""

class TableState:
    """Represents the state of a single table."""
    IDLE = "idle"
    TIMER_ACTIVE = "timer_active"
    TABLE_OPEN = "table_open"
    TIMER_EXPIRED = "timer_expired"


def init_table(table_id: int) -> Dict:
    """Initialize a table's data structure."""
    return {
        'id': table_id,
        'state': TableState.IDLE,
        'timer_start': None,
        'timer_duration': 60,  # Default 60 minutes
        'timer_end': None,
        'elapsed_time': 0,
        'is_open': False,
        # UI element references
        'status_label': None,
        'timer_label': None,
        'start_button': None,
        'open_button': None,
        'finish_button': None,
        'close_button': None,
    }


def format_time(seconds: int) -> str:
    """Format seconds into MM:SS format."""
    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes:02d}:{secs:02d}"


def get_remaining_time(table_id: int) -> int:
    """Get remaining time in seconds for a table's timer."""
    table = tables[table_id]
    if table['state'] != TableState.TIMER_ACTIVE or not table['timer_end']:
        return 0
    
    now = datetime.now()
    remaining = (table['timer_end'] - now).total_seconds()
    return max(0, int(remaining))


def get_elapsed_time(table_id: int) -> int:
    """Get elapsed time in seconds for a table's timer."""
    table = tables[table_id]
    if table['state'] != TableState.TIMER_ACTIVE or not table['timer_start']:
        return table.get('elapsed_time', 0)
    
    now = datetime.now()
    elapsed = (now - table['timer_start']).total_seconds()
    return int(elapsed)


# ============================================================================
# VISIBILITY FUNCTIONS - These have the bug that needs to be fixed
# ============================================================================

def hide_element(element):
    """Hide a UI element using props (BROKEN - doesn't work reliably)."""
    if element:
        element.props('style="display: none"')


def show_element(element):
    """Show a UI element using props (BROKEN - doesn't work reliably)."""
    if element:
        element.props('style="display: block"')


# ============================================================================
# TABLE ACTION HANDLERS
# ============================================================================

async def start_timer(table_id: int):
    """Start the timer for a table."""
    table = tables[table_id]
    
    # Set timer
    table['timer_start'] = datetime.now()
    table['timer_end'] = table['timer_start'] + timedelta(minutes=table['timer_duration'])
    table['state'] = TableState.TIMER_ACTIVE
    
    # Update UI
    refresh_ui(table_id)
    
    # Start background timer update
    asyncio.create_task(update_timer_loop(table_id))


async def finish_timer(table_id: int):
    """Finish/complete the timer for a table."""
    table = tables[table_id]
    
    # Calculate elapsed time
    if table['timer_start']:
        table['elapsed_time'] = get_elapsed_time(table_id)
    
    # Reset timer state
    table['timer_start'] = None
    table['timer_end'] = None
    table['state'] = TableState.IDLE
    
    # Update UI
    refresh_ui(table_id)


async def open_table(table_id: int):
    """Open a table for use."""
    table = tables[table_id]
    
    table['is_open'] = True
    table['state'] = TableState.TABLE_OPEN
    
    # Update UI
    refresh_ui(table_id)


async def close_table(table_id: int):
    """Close a table."""
    table = tables[table_id]
    
    table['is_open'] = False
    table['state'] = TableState.IDLE
    
    # Update UI
    refresh_ui(table_id)


async def update_timer_loop(table_id: int):
    """Background task to update timer display."""
    table = tables[table_id]
    
    while table['state'] == TableState.TIMER_ACTIVE:
        remaining = get_remaining_time(table_id)
        
        if remaining <= 0:
            # Timer expired
            table['state'] = TableState.TIMER_EXPIRED
            table['elapsed_time'] = get_elapsed_time(table_id)
            refresh_ui(table_id)
            break
        
        # Update timer display
        if table['timer_label']:
            table['timer_label'].text = format_time(remaining)
        
        await asyncio.sleep(1)


# ============================================================================
# UI REFRESH LOGIC
# ============================================================================

def refresh_ui(table_id: int):
    """Refresh the UI state for a table based on its current state."""
    table = tables[table_id]
    state = table['state']
    
    # Update status label
    if table['status_label']:
        status_text = {
            TableState.IDLE: "Idle",
            TableState.TIMER_ACTIVE: "Timer Active",
            TableState.TABLE_OPEN: "Table Open",
            TableState.TIMER_EXPIRED: "Timer Expired"
        }.get(state, "Unknown")
        
        status_class = {
            TableState.IDLE: "status-idle",
            TableState.TIMER_ACTIVE: "status-active",
            TableState.TABLE_OPEN: "status-open",
            TableState.TIMER_EXPIRED: "status-expired"
        }.get(state, "status-idle")
        
        table['status_label'].text = status_text
        table['status_label'].classes(replace=f"status-badge {status_class}")
    
    # Update timer display
    if table['timer_label']:
        if state == TableState.TIMER_ACTIVE:
            remaining = get_remaining_time(table_id)
            table['timer_label'].text = format_time(remaining)
        elif state == TableState.TIMER_EXPIRED:
            table['timer_label'].text = "EXPIRED"
        else:
            table['timer_label'].text = "--:--"
    
    # ========================================================================
    # BUTTON VISIBILITY LOGIC - This is where the bug occurs
    # The hide_element/show_element functions don't work properly
    # ========================================================================
    
    # Get button references
    start_btn = table['start_button']
    open_btn = table['open_button']
    finish_btn = table['finish_button']
    close_btn = table['close_button']
    
    if state == TableState.IDLE or state == TableState.TIMER_EXPIRED:
        # Show: Start Timer, Open
        # Hide: Finish, Close
        show_element(start_btn)
        show_element(open_btn)
        hide_element(finish_btn)
        hide_element(close_btn)
        
    elif state == TableState.TIMER_ACTIVE:
        # Show: Finish only
        # Hide: Start Timer, Open, Close
        hide_element(start_btn)
        hide_element(open_btn)
        show_element(finish_btn)
        hide_element(close_btn)
        
    elif state == TableState.TABLE_OPEN:
        # Show: Close only
        # Hide: Start Timer, Open, Finish
        hide_element(start_btn)
        hide_element(open_btn)
        hide_element(finish_btn)
        show_element(close_btn)


# ============================================================================
# UI BUILDING
# ============================================================================

def build_table_card(table_id: int):
    """Build the UI card for a single table."""
    table = tables[table_id]
    
    with ui.card().classes('table-card'):
        # Header
        ui.label(f'Table {table_id}').classes('table-header')
        
        # Status badge
        table['status_label'] = ui.label('Idle').classes('status-badge status-idle')
        
        # Timer display
        table['timer_label'] = ui.label('--:--').classes('timer-display')
        
        # Button row
        with ui.row().classes('button-row'):
            # NOTE: These buttons are created WITHOUT initial hidden state
            # This is part of the bug - they all show initially
            table['start_button'] = ui.button('Start Timer', 
                                              on_click=lambda t=table_id: start_timer(t))
            table['open_button'] = ui.button('Open', 
                                            on_click=lambda t=table_id: open_table(t))
            table['finish_button'] = ui.button('Finish', 
                                              on_click=lambda t=table_id: finish_timer(t))
            table['close_button'] = ui.button('Close', 
                                             on_click=lambda t=table_id: close_table(t))


def build_ui():
    """Build the main UI."""
    ui.add_head_html(CUSTOM_CSS)
    
    with ui.column().classes('w-full'):
        ui.label('Table Management System').classes('text-2xl font-bold mb-4')
        
        # Create a grid of tables
        with ui.grid(columns=3).classes('w-full gap-4'):
            for table_id in range(1, 7):  # 6 tables
                tables[table_id] = init_table(table_id)
                build_table_card(table_id)
        
        # NOTE: refresh_ui() is NOT called here after building the UI
        # This is part of the bug - initial state is not applied


# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """Main application entry point."""
    build_ui()
    
    # Start the NiceGUI server
    ui.run(
        title='Relays - Table Management',
        port=8080,
        reload=False,
        show=False
    )


if __name__ in {"__main__", "__mp_main__"}:
    main()
