#include "idleinhibitor.hpp"

#include <QtDBus/QDBusConnection>
#include <QtDBus/QDBusError>
#include <QtDBus/QDBusMessage>
#include <QDebug>
#include <QVariant>

namespace caelestia::internal {

IdleInhibitor::IdleInhibitor(QObject* parent)
    : QObject(parent) {
}

bool IdleInhibitor::enabled() const {
    return mEnabled;
}

void IdleInhibitor::setEnabled(bool enabled) {
    if (mEnabled == enabled)
        return;

    mEnabled = enabled;
    emit enabledChanged();
    updateInhibition();
}

QObject* IdleInhibitor::window() const {
    return mWindow;
}

void IdleInhibitor::setWindow(QObject* window) {
    if (mWindow == window)
        return;

    mWindow = window;
    emit windowChanged();
    updateInhibition();
}

void IdleInhibitor::updateInhibition() {
    if (!mEnabled || mWindow == nullptr) {
        releaseInhibitor();
        return;
    }

    if (mInhibitFd.isValid())
        return;

    auto bus = QDBusConnection::systemBus();
    if (!bus.isConnected()) {
        qWarning() << "IdleInhibitor: failed to connect to system bus:" << bus.lastError().message();
        return;
    }

    QDBusMessage message = QDBusMessage::createMethodCall(
        "org.freedesktop.login1",
        "/org/freedesktop/login1",
        "org.freedesktop.login1.Manager",
        "Inhibit");

    message << QStringLiteral("sleep")
            << QStringLiteral("caelestia-shell")
            << QStringLiteral("User requested idle inhibition")
            << QStringLiteral("block");

    const QDBusMessage reply = bus.call(message);
    const auto args = reply.arguments();
    if (reply.type() != QDBusMessage::ReplyMessage || args.isEmpty()) {
        qWarning() << "IdleInhibitor: failed to acquire inhibitor:" << reply.errorName() << reply.errorMessage();
        return;
    }

    const auto descriptor = args.constFirst().value<QDBusUnixFileDescriptor>();
    if (!descriptor.isValid()) {
        qWarning() << "IdleInhibitor: received invalid file descriptor from logind";
        return;
    }

    mInhibitFd = descriptor;
}

void IdleInhibitor::releaseInhibitor() {
    if (!mInhibitFd.isValid())
        return;

    mInhibitFd = QDBusUnixFileDescriptor();
}

} // namespace caelestia::internal
