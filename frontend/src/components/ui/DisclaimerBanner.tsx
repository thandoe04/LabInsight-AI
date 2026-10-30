import React from 'react';
import { AlertTriangle } from 'lucide-react';

interface Props {
  text?: string;
  className?: string;
}

export const DisclaimerBanner: React.FC<Props> = ({
  text = 'CLINICAL SAFETY RESTRICTION: LabInsight AI is a laboratory administration, research, and statistical analytics platform. It is NOT a medical diagnostic system. Statistical anomalies, reference intervals, and model predictions do not represent a diagnosis or therapeutic recommendation.',
  className = '',
}) => {
  return (
    <div className={`flex items-start gap-3 p-3 text-xs bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800/60 rounded-lg text-amber-800 dark:text-amber-300 ${className}`}>
      <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5 text-amber-600 dark:text-amber-400" />
      <div>
        <span className="font-semibold uppercase tracking-wider">Clinical Safety Notice: </span>
        <span>{text}</span>
      </div>
    </div>
  );
};
