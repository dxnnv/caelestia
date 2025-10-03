#pragma once

#include <QObject>
#include <QtDBus/QDBusUnixFileDescriptor>
#include <qqmlintegration.h>

namespace caelestia::internal {

class IdleInhibitor : public QObject {
    Q_OBJECT
    QML_ELEMENT

    Q_PROPERTY(bool enabled READ enabled WRITE setEnabled NOTIFY enabledChanged)
    Q_PROPERTY(QObject* window READ window WRITE setWindow NOTIFY windowChanged)

public:
    explicit IdleInhibitor(QObject* parent = nullptr);

    bool enabled() const;
    void setEnabled(bool enabled);

    QObject* window() const;
    void setWindow(QObject* window);

signals:
    void enabledChanged();
    void windowChanged();

private:
    void updateInhibition();
    void releaseInhibitor();

    bool mEnabled = false;
    QObject* mWindow = nullptr;
    QDBusUnixFileDescriptor mInhibitFd;
};

} // namespace caelestia::internal

