/** @odoo-module */

/**
 * List of colors according to the selection value, see `project_update.py`
 */
export const STATUS_COLORS = {
    'on_track': 10,
    'at_risk': 2,
    'off_track': 1,
    'on_hold': 8,
    'open': 0,
    'process': 3,
    'done': 20,
    'cancel': 23,
};

export const STATUS_COLOR_PREFIX = 'o_status_bubble mx-0 o_color_bubble_';