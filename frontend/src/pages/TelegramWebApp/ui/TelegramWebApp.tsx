import { useState } from 'react';
import {
  useTelegramSubscriptions,
  useCreateTelegramSubscription,
  useUpdateTelegramSubscription,
  useDeleteTelegramSubscription,
  useTelegramNotificationStats,
} from '@/api/telegram';
import {
  initTelegramApp,
  isTelegramWebApp,
  formatPrice,
  formatRooms,
  CITY_NAMES,
} from '@/shared/lib/telegram-webapp';
import type {
  TelegramSubscription,
  TelegramSubscriptionCreate,
  TelegramSubscriptionUpdate,
} from '@/shared/types/telegram';
import './styles.css';

const CITIES = [
  { code: 'minsk', name: 'Минск', emoji: '🏙️' },
  { code: 'mogilev', name: 'Могилёв', emoji: '🏛️' },
  { code: 'grodno', name: 'Гродно', emoji: '🏰' },
  { code: 'brest', name: 'Брест', emoji: '🛡️' },
  { code: 'gomel', name: 'Гомель', emoji: '🌳' },
  { code: 'vitebsk', name: 'Витебск', emoji: '🎭' },
];

const ROOMS = [
  { value: 'any', label: 'Любые' },
  { value: '1', label: '1' },
  { value: '2', label: '2' },
  { value: '3', label: '3' },
  { value: '4', label: '4' },
  { value: '5', label: '5+' },
];

type Tab = 'subscriptions' | 'stats';

function App() {
  const [activeTab, setActiveTab] = useState<Tab>('subscriptions');
  const [showModal, setShowModal] = useState(false);
  const [editingSubscription, setEditingSubscription] = useState<TelegramSubscription | null>(null);
  const [formData, setFormData] = useState<TelegramSubscriptionCreate>({
    city: 'minsk',
    rooms: null,
    price_min: null,
    price_max: null,
    currency: 'usd',
    price_per_m2_max: null,
    floor_min: null,
    floor_max: null,
    notify_only_price_drop: false,
    exclude_deal_below_percent: null,
  });

  const { data: subscriptions, isLoading: subscriptionsLoading } = useTelegramSubscriptions();
  const { data: stats } = useTelegramNotificationStats();
  const createMutation = useCreateTelegramSubscription();
  const updateMutation = useUpdateTelegramSubscription();
  const deleteMutation = useDeleteTelegramSubscription();

  const app = initTelegramApp();
  const isTelegram = isTelegramWebApp();

  const resetForm = () => {
    setFormData({
      city: 'minsk',
      rooms: null,
      price_min: null,
      price_max: null,
      currency: 'usd',
      price_per_m2_max: null,
      floor_min: null,
      floor_max: null,
      notify_only_price_drop: false,
      exclude_deal_below_percent: null,
    });
    setEditingSubscription(null);
  };

  const openCreateModal = () => {
    resetForm();
    setShowModal(true);
  };

  const openEditModal = (sub: TelegramSubscription) => {
    setEditingSubscription(sub);
    setFormData({
      city: sub.city,
      rooms: sub.rooms,
      price_min: sub.price_min,
      price_max: sub.price_max,
      currency: sub.currency,
      price_per_m2_max: sub.price_per_m2_max,
      floor_min: sub.floor_min,
      floor_max: sub.floor_max,
      notify_only_price_drop: sub.notify_only_price_drop,
      exclude_deal_below_percent: sub.exclude_deal_below_percent,
    });
    setShowModal(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingSubscription) {
        await updateMutation.mutateAsync({
          id: editingSubscription.id,
          data: formData as TelegramSubscriptionUpdate,
        });
      } else {
        await createMutation.mutateAsync(formData);
      }
      setShowModal(false);
      resetForm();
      if (app) {
        app.HapticFeedback.notificationOccurred('success');
      }
    } catch (error) {
      console.error('Error saving subscription:', error);
      if (app) {
        app.HapticFeedback.notificationOccurred('error');
      }
    }
  };

  const handleDelete = async (id: string) => {
    if (confirm('Удалить эту подписку?')) {
      try {
        await deleteMutation.mutateAsync(id);
        if (app) {
          app.HapticFeedback.notificationOccurred('success');
        }
      } catch (error) {
        console.error('Error deleting subscription:', error);
      }
    }
  };

  const toggleActive = async (sub: TelegramSubscription) => {
    try {
      await updateMutation.mutateAsync({
        id: sub.id,
        data: { is_active: !sub.is_active },
      });
      if (app) {
        app.HapticFeedback.impactOccurred('medium');
      }
    } catch (error) {
      console.error('Error toggling subscription:', error);
    }
  };

  const renderCityEmoji = (cityCode: string) => {
    const city = CITIES.find(c => c.code === cityCode);
    return city?.emoji || '🏠';
  };

  const renderStats = () => {
    if (!stats) {
      return (
        <div className="loading">
          <div className="loading-spinner" />
        </div>
      );
    }

    const successRate = stats.total_notifications > 0 
      ? Math.round((stats.successful / stats.total_notifications) * 100) 
      : 0;

    return (
      <div className="stats-grid animate-in">
        <div className="stat-card-large">
          <div className="stat-icon">📊</div>
          <div className="stat-content">
            <div className="stat-value">{stats.total_notifications}</div>
            <div className="stat-label">Всего уведомлений</div>
          </div>
        </div>
        
        <div className="stat-card-large">
          <div className="stat-icon">✅</div>
          <div className="stat-content">
            <div className="stat-value">{stats.successful}</div>
            <div className="stat-label">Доставлено</div>
          </div>
        </div>
        
        <div className="stat-card-large">
          <div className="stat-icon">❌</div>
          <div className="stat-content">
            <div className="stat-value">{stats.failed}</div>
            <div className="stat-label">Ошибки</div>
          </div>
        </div>
        
        <div className="stat-card-large">
          <div className="stat-icon">📈</div>
          <div className="stat-content">
            <div className="stat-value">{successRate}%</div>
            <div className="stat-label">Успешность</div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="telegram-webapp">
      <div className="app-container">
        {/* Header */}
        <header className="app-header animate-in">
          <div className="header-content">
            <h1 className="app-title">Kufar Monitor</h1>
            <p className="app-subtitle">
              {isTelegram ? '🤖 Telegram Mini App' : '🌐 Web версия'}
            </p>
          </div>
          {isTelegram && (
            <div className="telegram-badge">Telegram</div>
          )}
        </header>

        {/* Tab Navigation */}
        <div className="tab-nav animate-in stagger-1">
          <button 
            className={`tab-btn ${activeTab === 'subscriptions' ? 'active' : ''}`}
            onClick={() => setActiveTab('subscriptions')}
          >
            📋 Подписки
          </button>
          <button 
            className={`tab-btn ${activeTab === 'stats' ? 'active' : ''}`}
            onClick={() => setActiveTab('stats')}
          >
            📊 Статистика
          </button>
        </div>

        {/* Content */}
        {activeTab === 'subscriptions' && (
          <section className="section animate-in stagger-2">
            {subscriptionsLoading ? (
              <div className="loading">
                <div className="loading-spinner" />
              </div>
            ) : subscriptions && subscriptions.length > 0 ? (
              <div className="subscription-list">
                {subscriptions.map((sub, index) => (
                  <div
                    key={sub.id}
                    className={`subscription-card ${sub.is_active ? 'active' : ''} animate-in stagger-${Math.min(index + 1, 5)}`}
                  >
                    <div className="subscription-header">
                      <div className="city-info">
                        <span className="city-emoji">{renderCityEmoji(sub.city)}</span>
                        <h3 className="subscription-city">
                          {CITY_NAMES[sub.city] || sub.city}
                        </h3>
                      </div>
                      <span className={`subscription-status ${sub.is_active ? 'active' : 'inactive'}`}>
                        {sub.is_active ? 'Активна' : 'Пауза'}
                      </span>
                    </div>

                    <div className="subscription-params">
                      {sub.rooms && (
                        <span className="subscription-param">
                          <span className="subscription-param-icon">🚪</span>
                          {formatRooms(sub.rooms)}
                        </span>
                      )}
                      {(sub.price_min || sub.price_max) && (
                        <span className="subscription-param">
                          <span className="subscription-param-icon">💰</span>
                          {formatPrice(sub.price_min, sub.currency)}
                          {sub.price_max && ` — ${formatPrice(sub.price_max, sub.currency)}`}
                        </span>
                      )}
                      {sub.price_per_m2_max && (
                        <span className="subscription-param">
                          <span className="subscription-param-icon">📏</span>
                          до {formatPrice(sub.price_per_m2_max, sub.currency)}/м²
                        </span>
                      )}
                      {(sub.floor_min || sub.floor_max) && (
                        <span className="subscription-param">
                          <span className="subscription-param-icon">🏢</span>
                          {sub.floor_min}{sub.floor_max ? `-${sub.floor_max}` : '+'} эт.
                        </span>
                      )}
                      {sub.notify_only_price_drop && (
                        <span className="subscription-param accent">
                          <span className="subscription-param-icon">📉</span>
                          Только падение
                        </span>
                      )}
                      {sub.exclude_deal_below_percent && (
                        <span className="subscription-param accent">
                          <span className="subscription-param-icon">🎯</span>
                          Deal ≥{sub.exclude_deal_below_percent}%
                        </span>
                      )}
                    </div>

                    <div className="subscription-actions">
                      <button className="btn btn-secondary" onClick={() => openEditModal(sub)}>
                        ✏️
                      </button>
                      <button 
                        className={`btn ${sub.is_active ? 'btn-warning' : 'btn-success'}`} 
                        onClick={() => toggleActive(sub)}
                      >
                        {sub.is_active ? '⏸' : '▶️'}
                      </button>
                      <button className="btn btn-danger" onClick={() => handleDelete(sub.id)}>
                        🗑
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-state">
                <div className="empty-icon">📭</div>
                <h3 className="empty-title">Нет подписок</h3>
                <p className="empty-text">Создайте первую подписку, чтобы получать уведомления о новых квартирах</p>
              </div>
            )}
          </section>
        )}

        {activeTab === 'stats' && (
          <section className="section animate-in stagger-2">
            {renderStats()}
          </section>
        )}

        {/* FAB */}
        {activeTab === 'subscriptions' && subscriptions && subscriptions.length < 5 && (
          <button className="fab animate-in stagger-3" onClick={openCreateModal}>
            +
          </button>
        )}

        {/* Modal */}
        {showModal && (
          <div className="modal-overlay" onClick={() => setShowModal(false)}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <h2 className="modal-title">
                  {editingSubscription ? 'Редактировать' : 'Новая подписка'}
                </h2>
                <button className="modal-close" onClick={() => setShowModal(false)}>
                  ✕
                </button>
              </div>

              <form onSubmit={handleSubmit}>
                {/* City */}
                <div className="form-group">
                  <label className="form-label">🏙️ Город</label>
                  <select
                    className="form-select"
                    value={formData.city}
                    onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                    required
                  >
                    {CITIES.map((city) => (
                      <option key={city.code} value={city.code}>
                        {city.emoji} {city.name}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Rooms */}
                <div className="form-group">
                  <label className="form-label">🚪 Комнаты</label>
                  <div className="form-checkbox-group">
                    {ROOMS.map((room) => (
                      <label key={room.value} className="cursor-pointer">
                        <input
                          type="radio"
                          name="rooms"
                          className="form-checkbox"
                          checked={
                            room.value === 'any'
                              ? formData.rooms === null
                              : formData.rooms?.[0] === parseInt(room.value) ||
                                (room.value === '5' && formData.rooms?.[0] === 5)
                          }
                          onChange={() =>
                            setFormData({
                              ...formData,
                              rooms: room.value === 'any' ? null : [parseInt(room.value)],
                            })
                          }
                        />
                        <span className="form-checkbox-label">{room.label}</span>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Currency */}
                <div className="form-group">
                  <label className="form-label">💱 Валюта</label>
                  <div className="toggle-group">
                    <div
                      className={`toggle-option ${formData.currency === 'usd' ? 'active' : ''}`}
                      onClick={() => setFormData({ ...formData, currency: 'usd' })}
                    >
                      USD ($)
                    </div>
                    <div
                      className={`toggle-option ${formData.currency === 'byn' ? 'active' : ''}`}
                      onClick={() => setFormData({ ...formData, currency: 'byn' })}
                    >
                      BYN (Br)
                    </div>
                  </div>
                </div>

                {/* Price Range */}
                <div className="form-group">
                  <label className="form-label">💰 Цена</label>
                  <div className="price-inputs">
                    <input
                      type="number"
                      className="form-input"
                      placeholder="От"
                      value={formData.price_min || ''}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          price_min: e.target.value ? parseInt(e.target.value) : null,
                        })
                      }
                    />
                    <span className="price-separator">—</span>
                    <input
                      type="number"
                      className="form-input"
                      placeholder="До"
                      value={formData.price_max || ''}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          price_max: e.target.value ? parseInt(e.target.value) : null,
                        })
                      }
                    />
                  </div>
                </div>

                {/* Price per m2 */}
                <div className="form-group">
                  <label className="form-label">📏 Цена за м² (макс)</label>
                  <input
                    type="number"
                    className="form-input"
                    placeholder="Не ограничено"
                    value={formData.price_per_m2_max || ''}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        price_per_m2_max: e.target.value ? parseInt(e.target.value) : null,
                      })
                    }
                  />
                </div>

                {/* Floor Range */}
                <div className="form-group">
                  <label className="form-label">🏢 Этаж</label>
                  <div className="price-inputs">
                    <input
                      type="number"
                      className="form-input"
                      placeholder="От"
                      value={formData.floor_min || ''}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          floor_min: e.target.value ? parseInt(e.target.value) : null,
                        })
                      }
                    />
                    <span className="price-separator">—</span>
                    <input
                      type="number"
                      className="form-input"
                      placeholder="До"
                      value={formData.floor_max || ''}
                      onChange={(e) =>
                        setFormData({
                          ...formData,
                          floor_max: e.target.value ? parseInt(e.target.value) : null,
                        })
                      }
                    />
                  </div>
                </div>

                {/* Notify Only Price Drop */}
                <div className="form-group">
                  <label className="form-label">📉 Режим уведомлений</label>
                  <div className="toggle-group">
                    <div
                      className={`toggle-option ${!formData.notify_only_price_drop ? 'active' : ''}`}
                      onClick={() => setFormData({ ...formData, notify_only_price_drop: false })}
                    >
                      Все новые
                    </div>
                    <div
                      className={`toggle-option ${formData.notify_only_price_drop ? 'active' : ''}`}
                      onClick={() => setFormData({ ...formData, notify_only_price_drop: true })}
                    >
                      Только падение
                    </div>
                  </div>
                </div>

                {/* Deal Score */}
                <div className="form-group">
                  <label className="form-label">🎯 Deal Score (мин)</label>
                  <input
                    type="number"
                    className="form-input"
                    placeholder="Любой"
                    min="1"
                    max="100"
                    value={formData.exclude_deal_below_percent || ''}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        exclude_deal_below_percent: e.target.value
                          ? parseInt(e.target.value)
                          : null,
                      })
                    }
                  />
                </div>

                {/* Submit */}
                <button
                  type="submit"
                  className="btn btn-primary btn-full"
                  disabled={createMutation.isPending || updateMutation.isPending}
                >
                  {createMutation.isPending || updateMutation.isPending
                    ? '⏳ Сохранение...'
                    : editingSubscription
                    ? '💾 Сохранить'
                    : '✨ Создать подписку'}
                </button>
              </form>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;