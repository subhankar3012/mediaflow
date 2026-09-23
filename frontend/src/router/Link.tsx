import React from 'react';
import type { AnchorHTMLAttributes, MouseEvent } from 'react';
import { useRouter } from './Router';

export interface LinkProps extends Omit<AnchorHTMLAttributes<HTMLAnchorElement>, 'href'> {
  to?: string;
  href?: string;
  className?: string;
  activeClassName?: string;
  children: React.ReactNode;
}

export const Link: React.FC<LinkProps> = ({
  to,
  href,
  className = '',
  activeClassName = '',
  children,
  onClick,
  ...props
}) => {
  const target = to || href || '/';
  const { pathname, navigate } = useRouter();
  const isActive = pathname === target;

  const handleClick = (e: MouseEvent<HTMLAnchorElement>) => {
    // Prevent any ad network listeners from hijacking internal tool navigation
    e.stopPropagation();
    if (e.nativeEvent) {
      e.nativeEvent.stopImmediatePropagation?.();
    }

    if (onClick) {
      onClick(e);
    }
    // Allow standard browser shortcuts: Ctrl+Click, Cmd+Click, Shift+Click, Middle click
    if (
      !e.defaultPrevented &&
      e.button === 0 &&
      !e.metaKey &&
      !e.ctrlKey &&
      !e.altKey &&
      !e.shiftKey
    ) {
      e.preventDefault();
      navigate(target);
    }
  };

  const combinedClass = `${className} ${isActive ? activeClassName : ''}`.trim();

  return (
    <a
      href={target}
      className={combinedClass}
      onClick={handleClick}
      onMouseDown={(e) => {
        e.stopPropagation();
        e.nativeEvent?.stopImmediatePropagation?.();
      }}
      onTouchStart={(e) => {
        e.stopPropagation();
        e.nativeEvent?.stopImmediatePropagation?.();
      }}
      aria-current={isActive ? 'page' : undefined}
      {...props}
    >
      {children}
    </a>
  );
};
