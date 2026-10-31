import type { ButtonHTMLAttributes } from 'react';
import { cx } from '../../cx';
import styles from './Button.module.css';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost';
  size?: 'regular' | 'large';
}

export function Button({ variant = 'secondary', size = 'regular', className, type = 'button', ...rest }: ButtonProps) {
  return (
    <button
      type={type}
      className={cx(styles.button, styles[variant], size === 'large' && styles.large, className)}
      {...rest}
    />
  );
}
