import React from 'react';
import { Link } from '../../router/Link';
import type { BreadcrumbItem } from '../../utils/seoHelpers';

export interface BreadcrumbsProps {
  items?: BreadcrumbItem[];
}

export const Breadcrumbs: React.FC<BreadcrumbsProps> = ({ items }) => {
  if (!items || items.length <= 1) {
    return null;
  }

  return (
    <nav aria-label="Breadcrumbs" className="breadcrumbs-nav site-container">
      <ol className="breadcrumbs-list">
        {items.map((item, index) => {
          const isLast = index === items.length - 1;
          return (
            <li key={item.path} className="breadcrumbs-item">
              {isLast ? (
                <span className="breadcrumbs-current" aria-current="page">
                  {item.name}
                </span>
              ) : (
                <>
                  <Link to={item.path} className="breadcrumbs-link">
                    {item.name}
                  </Link>
                  <span className="breadcrumbs-separator" aria-hidden="true">
                    /
                  </span>
                </>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
};
