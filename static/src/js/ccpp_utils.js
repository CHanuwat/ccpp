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
    'waiting_approve': 8,
    'process': 3,
    'done': 20,
    'cancel': 23,
    'delay': 24,
    'over': 20,
    'similar': 3,
    'less': 23,
    '1': 9,
    '2': 2,
    '3': 3,
    '4': 4,
    'to_define': 0,
};

export const STATUS_COLOR_PREFIX = 'o_status_bubble mx-0 o_color_bubble_';