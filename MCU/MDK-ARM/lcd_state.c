#ifndef LCD_STATE_H
#define LCD_STATE_H

typedef enum {
    LCD_STATE_NORMAL,     // Hi?n th? nhi?t d? v� d? d?c
    LCD_STATE_FEEDING,    // Khi b?m BUTTON -> "FEEDING..."
    LCD_STATE_TIMESET     // Khi set time
} LCD_State_t;

/* Khai b�o bi?n to�n c?c d? c�c module kh�c d�ng */
extern LCD_State_t lcd_state;

/* N?u c?n, b?n c� th? khai b�o h�m c?p nh?t LCD ? d�y:
   void LCD_Update(void);
   nhung n?u h�m n�y d?nh nghia trong main.c v� b?n include main.h,
   kh�ng b?t bu?c. */

#endif /* LCD_STATE_H */
