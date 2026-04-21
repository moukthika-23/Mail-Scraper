import React from 'react';
import { useAppStore } from '../../store/appStore';
import { CheckCircleIcon, XCircleIcon, InformationCircleIcon, ExclamationTriangleIcon, XMarkIcon } from '@heroicons/react/24/outline';
import './Notifications.css';

const ICONS = {
  success: <CheckCircleIcon width={16} />,
  error:   <XCircleIcon width={16} />,
  info:    <InformationCircleIcon width={16} />,
  warning: <ExclamationTriangleIcon width={16} />,
};

const Notifications: React.FC = () => {
  const { notifications, removeNotification } = useAppStore();

  return (
    <div className="notifications" aria-live="polite">
      {notifications.map((n) => (
        <div key={n.id} className={`notification notification--${n.type} animate-slide-left`}>
          <span className={`notification__icon notification__icon--${n.type}`}>{ICONS[n.type]}</span>
          <div className="notification__body">
            <div className="notification__title">{n.title}</div>
            {n.message && <div className="notification__msg">{n.message}</div>}
          </div>
          <button className="notification__close" onClick={() => removeNotification(n.id)}>
            <XMarkIcon width={13} />
          </button>
        </div>
      ))}
    </div>
  );
};

export default Notifications;
