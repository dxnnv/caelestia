#include "idlemonitor.hpp"

#include <QDebug>
#include <QtDBus/QDBusConnection>
#include <QtDBus/QDBusError>
#include <QtDBus/QDBusMessage>
#include <QtDBus/QDBusVariant>

#include <time.h>

namespace caelestia::internal {

namespace {
constexpr auto logindService = "org.freedesktop.login1";
constexpr auto logindPath = "/org/freedesktop/login1";
constexpr auto logindManager = "org.freedesktop.login1.Manager";
constexpr auto propertiesInterface = "org.freedesktop.DBus.Properties";
constexpr auto sessionInterface = "org.freedesktop.login1.Session";
} // namespace

IdleMonitor::IdleMonitor(QObject* parent)
    : QObject(parent) {
    mPollTimer.setInterval(1000);
    mPollTimer.setTimerType(Qt::VeryCoarseTimer);
    connect(&mPollTimer, &QTimer::timeout, this, &IdleMonitor::updateIdleState);
    ensureSession();
    mPollTimer.start();
}

bool IdleMonitor::enabled() const {
    return mEnabled;
}

void IdleMonitor::setEnabled(bool enabled) {
    if (mEnabled == enabled)
        return;

    mEnabled = enabled;
    emit enabledChanged();
    updateIdleState();
}

int IdleMonitor::timeout() const {
    return mTimeout;
}

void IdleMonitor::setTimeout(int seconds) {
    if (mTimeout == seconds)
        return;

    mTimeout = seconds;
    emit timeoutChanged();
    updateIdleState();
}

bool IdleMonitor::respectInhibitors() const {
    return mRespectInhibitors;
}

void IdleMonitor::setRespectInhibitors(bool respect) {
    if (mRespectInhibitors == respect)
        return;

    mRespectInhibitors = respect;
    emit respectInhibitorsChanged();
    updateIdleState();
}

bool IdleMonitor::isIdle() const {
    return mIsIdle;
}

void IdleMonitor::handlePropertiesChanged(const QString& interface, const QVariantMap& changed, const QStringList&) {
    if (interface != QLatin1String(sessionInterface))
        return;

    if (changed.contains("IdleSinceHint") || changed.contains("IdleHint"))
        updateIdleState();
}

void IdleMonitor::updateIdleState() {
    bool idle = false;

    if (mEnabled && mTimeout > 0) {
        if (!mSessionPath.isEmpty()) {
            if (!mRespectInhibitors || !hasIdleInhibitor()) {
                const auto idleSince = queryIdleSinceHint();
                const auto now = currentBootUsec();
                if (idleSince > 0 && now >= idleSince) {
                    const auto idleSeconds = (now - idleSince) / 1'000'000ull;
                    idle = idleSeconds >= static_cast<quint64>(mTimeout);
                }
            }
        } else {
            ensureSession();
        }
    }

    if (idle == mIsIdle)
        return;

    mIsIdle = idle;
    emit isIdleChanged();
}

void IdleMonitor::ensureSession() {
    auto bus = QDBusConnection::systemBus();
    if (!bus.isConnected()) {
        qWarning() << "IdleMonitor: failed to connect to system bus:" << bus.lastError().message();
        return;
    }

    QDBusMessage message = QDBusMessage::createMethodCall(logindService, logindPath, logindManager, "GetSession");
    message << QStringLiteral("auto");
    const QDBusMessage reply = bus.call(message);
    const auto args = reply.arguments();
    if (reply.type() != QDBusMessage::ReplyMessage || args.isEmpty()) {
        qWarning() << "IdleMonitor: failed to resolve session path:" << reply.errorName() << reply.errorMessage();
        return;
    }

    const auto path = args.constFirst().value<QDBusObjectPath>().path();
    if (path.isEmpty()) {
        qWarning() << "IdleMonitor: received empty session path from logind";
        return;
    }

    if (mSessionPath == path)
        return;

    if (!mSessionPath.isEmpty()) {
        bus.disconnect(logindService, mSessionPath, propertiesInterface, "PropertiesChanged", this, SLOT(handlePropertiesChanged(QString,QVariantMap,QStringList)));
    }

    mSessionPath = path;

    const bool ok = bus.connect(logindService, mSessionPath, propertiesInterface, "PropertiesChanged",
        this, SLOT(handlePropertiesChanged(QString,QVariantMap,QStringList)));

    if (!ok)
        qWarning() << "IdleMonitor: failed to subscribe to session updates:" << bus.lastError().message();

    updateIdleState();
}

quint64 IdleMonitor::queryIdleSinceHint() const {
    auto bus = QDBusConnection::systemBus();
    if (!bus.isConnected() || mSessionPath.isEmpty())
        return 0;

    QDBusMessage message = QDBusMessage::createMethodCall(logindService, mSessionPath, propertiesInterface, "Get");
    message << QString::fromLatin1(sessionInterface) << QStringLiteral("IdleSinceHint");
    const QDBusMessage reply = bus.call(message);
    const auto args = reply.arguments();

    if (reply.type() != QDBusMessage::ReplyMessage || args.isEmpty())
        return 0;

    const QVariant variant = args.constFirst().value<QDBusVariant>().variant();
    if (!variant.canConvert<qulonglong>())
        return 0;

    return variant.toULongLong();
}

bool IdleMonitor::hasIdleInhibitor() const {
    if (!mRespectInhibitors)
        return false;

    auto bus = QDBusConnection::systemBus();
    if (!bus.isConnected() || mSessionPath.isEmpty())
        return false;

    QDBusMessage message = QDBusMessage::createMethodCall(logindService, mSessionPath, propertiesInterface, "Get");
    message << QString::fromLatin1(sessionInterface) << QStringLiteral("IdleHint");
    const QDBusMessage reply = bus.call(message);
    const auto args = reply.arguments();
    if (reply.type() != QDBusMessage::ReplyMessage || args.isEmpty())
        return false;

    const QVariant variant = args.constFirst().value<QDBusVariant>().variant();
    if (!variant.canConvert<bool>())
        return false;

    return !variant.toBool();
}

quint64 IdleMonitor::currentBootUsec() {
    timespec ts {0, 0};
    if (clock_gettime(CLOCK_BOOTTIME, &ts) != 0)
        return 0;

    return static_cast<quint64>(ts.tv_sec) * 1'000'000ull + static_cast<quint64>(ts.tv_nsec) / 1000ull;
}

} // namespace caelestia::internal
