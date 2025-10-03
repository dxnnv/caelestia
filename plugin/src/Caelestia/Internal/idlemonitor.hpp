#pragma once

#include <QObject>
#include <QStringList>
#include <QTimer>
#include <QVariantMap>
#include <QtDBus/QDBusObjectPath>
#include <qqmlintegration.h>

namespace caelestia::internal {

class IdleMonitor : public QObject {
    Q_OBJECT
    QML_ELEMENT

    Q_PROPERTY(bool enabled READ enabled WRITE setEnabled NOTIFY enabledChanged)
    Q_PROPERTY(int timeout READ timeout WRITE setTimeout NOTIFY timeoutChanged)
    Q_PROPERTY(bool respectInhibitors READ respectInhibitors WRITE setRespectInhibitors NOTIFY respectInhibitorsChanged)
    Q_PROPERTY(bool isIdle READ isIdle NOTIFY isIdleChanged)

public:
    explicit IdleMonitor(QObject* parent = nullptr);

    bool enabled() const;
    void setEnabled(bool enabled);

    int timeout() const;
    void setTimeout(int seconds);

    bool respectInhibitors() const;
    void setRespectInhibitors(bool respect);

    bool isIdle() const;

signals:
    void enabledChanged();
    void timeoutChanged();
    void respectInhibitorsChanged();
    void isIdleChanged();

private slots:
    void handlePropertiesChanged(const QString& interface, const QVariantMap& changed, const QStringList& invalidated);
    void updateIdleState();

private:
    void ensureSession();
    quint64 queryIdleSinceHint() const;
    bool hasIdleInhibitor() const;
    static quint64 currentBootUsec();

    bool mEnabled = true;
    int mTimeout = 0;
    bool mRespectInhibitors = true;
    bool mIsIdle = false;
    QString mSessionPath;
    QTimer mPollTimer;
};

} // namespace caelestia::internal
