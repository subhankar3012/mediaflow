import React, { useState } from 'react';

export interface FAQItem {
  question: string;
  answer: string;
}

export interface FAQSectionProps {
  faqs: FAQItem[];
  title?: string;
}

export const FAQSection: React.FC<FAQSectionProps> = ({
  faqs,
  title = 'Frequently Asked Questions',
}) => {
  // First question open by default
  const [openIndexes, setOpenIndexes] = useState<Record<number, boolean>>({ 0: true });

  const toggleIndex = (index: number) => {
    setOpenIndexes((prev) => ({
      ...prev,
      [index]: !prev[index],
    }));
  };

  if (!faqs || faqs.length === 0) return null;

  return (
    <section className="faq-section-editorial" id="faq" aria-labelledby="faq-heading">
      <div className="site-container-narrow">
        <div className="section-header-editorial">
          <span className="section-eyebrow">Clarity</span>
          <h2 id="faq-heading" className="section-h2-editorial">
            {title}
          </h2>
        </div>

        <div className="faq-divide-list">
          {faqs.map((faq, idx) => {
            const isOpen = Boolean(openIndexes[idx]);
            const questionId = `faq-q-${idx}`;
            const answerId = `faq-a-${idx}`;

            return (
              <div key={idx} className="faq-divide-item">
                <button
                  type="button"
                  id={questionId}
                  aria-expanded={isOpen}
                  aria-controls={answerId}
                  onClick={() => toggleIndex(idx)}
                  className="faq-divide-btn"
                >
                  <span className="faq-q-text">{faq.question}</span>
                  <svg
                    className="faq-chevron"
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    style={{
                      transform: isOpen ? 'rotate(180deg)' : 'rotate(0deg)',
                      transition: 'transform var(--transition-fast)',
                    }}
                    aria-hidden="true"
                  >
                    <polyline points="6 9 12 15 18 9" />
                  </svg>
                </button>

                {isOpen && (
                  <div
                    id={answerId}
                    role="region"
                    aria-labelledby={questionId}
                    className="faq-divide-answer"
                  >
                    <p>{faq.answer}</p>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
};
