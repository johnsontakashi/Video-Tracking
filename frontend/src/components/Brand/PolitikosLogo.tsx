import React from 'react';
import './PolitikosLogo.css';

interface PolitikosLogoProps {
  variant?: 'positive' | 'negative' | 'monochrome';
  size?: 'small' | 'medium' | 'large' | 'xlarge';
  withProtection?: boolean;
  className?: string;
}

const PolitikosLogo: React.FC<PolitikosLogoProps> = ({
  variant = 'positive',
  size = 'medium',
  withProtection = false,
  className = ''
}) => {
  const logoClasses = [
    'politikos-logo',
    `politikos-logo--${variant}`,
    `politikos-logo--${size}`,
    withProtection ? 'politikos-logo--protected' : '',
    className
  ].filter(Boolean).join(' ');

  return (
    <div className={logoClasses}>
      <div className="politikos-logo__container">
        {/* POLITI - Analytical Data Part */}
        <div className="politikos-logo__politi">
          <span className="politikos-logo__letter politikos-logo__letter--p">P</span>
          <span className="politikos-logo__letter politikos-logo__letter--o">O</span>
          <span className="politikos-logo__letter politikos-logo__letter--l">L</span>
          <span className="politikos-logo__letter politikos-logo__letter--i">I</span>
          <span className="politikos-logo__letter politikos-logo__letter--t">T</span>
          <span className="politikos-logo__letter politikos-logo__letter--i2">I</span>
        </div>
        {/* KOS - Brazilian Flag Part */}
        <div className="politikos-logo__kos">
          {/* K - Yellow (Diamond shape reference) */}
          <span className="politikos-logo__letter politikos-logo__letter--k">K</span>
          {/* O - Blue (Central circle reference) */}
          <span className="politikos-logo__letter politikos-logo__letter--o-flag">O</span>
          {/* S - Green (Growth and hope reference) */}
          <span className="politikos-logo__letter politikos-logo__letter--s">S</span>
        </div>
      </div>
      
      {/* Tagline for larger sizes */}
      {(size === 'large' || size === 'xlarge') && (
        <div className="politikos-logo__tagline">
          <span className="politikos-tagline__text">
            Análise de Dados para Políticos e Gestores Públicos
          </span>
        </div>
      )}
    </div>
  );
};

// Simplified text version for headers
export const PolitikosLogoText: React.FC<{
  variant?: 'positive' | 'negative' | 'monochrome';
  size?: 'small' | 'medium' | 'large';
  className?: string;
}> = ({ variant = 'positive', size = 'medium', className = '' }) => {
  const textClasses = [
    'politikos-logo-text',
    `politikos-logo-text--${variant}`,
    `politikos-logo-text--${size}`,
    className
  ].filter(Boolean).join(' ');

  return (
    <span className={textClasses}>
      <span className="politikos-text__politi">POLITI</span>
      <span className="politikos-text__kos">
        <span className="politikos-text__k">K</span>
        <span className="politikos-text__o">O</span>
        <span className="politikos-text__s">S</span>
      </span>
    </span>
  );
};

// Icon version for favicons and small spaces
export const PolitikosIcon: React.FC<{
  variant?: 'positive' | 'negative' | 'monochrome';
  size?: string;
  className?: string;
}> = ({ variant = 'positive', size = '32px', className = '' }) => {
  return (
    <div 
      className={`politikos-icon politikos-icon--${variant} ${className}`}
      style={{ width: size, height: size }}
    >
      <div className="politikos-icon__circle politikos-icon__circle--blue"></div>
      <div className="politikos-icon__diamond politikos-icon__diamond--yellow"></div>
      <div className="politikos-icon__wave politikos-icon__wave--green"></div>
    </div>
  );
};

export default PolitikosLogo;