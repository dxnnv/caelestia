#include "appdb.hpp"

#include <QMetaMethod>
#include <QMetaObject>
#include <QMetaProperty>
#include <QPointer>
#include <QSet>
#include <algorithm>

#include <QSqlDatabase>
#include <QSqlQuery>
#include <QUuid>

namespace caelestia {

// ——— AppEntry ————————————————————————————————————————————————————————————————

static inline QString readStringProp(const QObject* o, const char* name) {
    if (!o)
        return {};
    return o->property(name).toString();
}

static inline QString joinStringListProp(const QObject* o, const char* name) {
    if (!o)
        return {};
    const QVariant v = o->property(name);
    if (v.metaType() == QMetaType::fromType<QStringList>()) {
        return v.toStringList().join(u' ');
    }
    // If some providers expose a single string already:
    return v.toString();
}

AppEntry::AppEntry(QObject* entry, quint32 frequency, QObject* parent)
    : QObject(parent)
    , m_entry(entry)
    , m_frequency(frequency) {
    // Mirror notify signals from the underlying DesktopEntry to our own notifies.
    mirrorNotifySignals();

    // When the underlying entry goes away, drop ourselves as well.
    QObject::connect(m_entry, &QObject::destroyed, this, [this]() {
        m_entry = nullptr;
        deleteLater();
    });
}

void AppEntry::mirrorNotifySignals() {
    if (!m_entry)
        return;

    const QMetaObject* srcMo = m_entry->metaObject();
    const QMetaObject* dstMo = this->metaObject();

    auto connectNotify = [&](const char* propName, const char* dstSignalSig) {
        const int pidx = srcMo->indexOfProperty(propName);
        if (pidx < 0)
            return; // property not found on source

        const QMetaProperty srcProp = srcMo->property(pidx);
        if (!srcProp.hasNotifySignal())
            return;

        const QMetaMethod srcSig = srcProp.notifySignal();

        const int didx = dstMo->indexOfSignal(dstSignalSig); // e.g. "nameChanged()"
        if (didx < 0)
            return;

        const QMetaMethod dstSig = dstMo->method(didx);

        // signal→signal is fine if both are void()
        QObject::connect(m_entry, srcSig, this, dstSig);
    };

    connectNotify("name", "nameChanged()");
    connectNotify("comment", "commentChanged()");
    connectNotify("execString", "execStringChanged()");
    connectNotify("startupClass", "startupClassChanged()");
    connectNotify("genericName", "genericNameChanged()");
    connectNotify("categories", "categoriesChanged()");
    connectNotify("keywords", "keywordsChanged()");
}

quint32 AppEntry::frequency() const {
    return m_frequency;
}

void AppEntry::setFrequency(quint32 frequency) {
    if (m_frequency == frequency)
        return;
    m_frequency = frequency;
    emit frequencyChanged();
}

void AppEntry::incrementFrequency() {
    ++m_frequency;
    emit frequencyChanged();
}

QString AppEntry::id() const {
    return readStringProp(m_entry, "id");
}

QString AppEntry::name() const {
    return readStringProp(m_entry, "name");
}

QString AppEntry::comment() const {
    return readStringProp(m_entry, "comment");
}

QString AppEntry::execString() const {
    return readStringProp(m_entry, "execString");
}

QString AppEntry::startupClass() const {
    return readStringProp(m_entry, "startupClass");
}

QString AppEntry::genericName() const {
    return readStringProp(m_entry, "genericName");
}

QString AppEntry::categories() const {
    return joinStringListProp(m_entry, "categories");
}

QString AppEntry::keywords() const {
    return joinStringListProp(m_entry, "keywords");
}

// ——— AppDb ————————————————————————————————————————————————————————————————

AppDb::AppDb(QObject* parent)
    : QObject(parent)
    , m_timer(new QTimer(this))
    , m_uuid(QUuid::createUuid().toString()) {
    m_timer->setSingleShot(true);
    m_timer->setInterval(300);
    QObject::connect(m_timer, &QTimer::timeout, this, &AppDb::updateApps);

    // in-memory DB for default
    auto db = QSqlDatabase::addDatabase("QSQLITE", m_uuid);
    db.setDatabaseName(":memory:");
    db.open();

    QSqlQuery query(db);
    query.exec("CREATE TABLE IF NOT EXISTS frequencies (id TEXT PRIMARY KEY, frequency INTEGER)");
}

QString AppDb::uuid() const {
    return m_uuid;
}

QString AppDb::path() const {
    return m_path;
}

void AppDb::setPath(const QString& path) {
    const QString newPath = path.isEmpty() ? QStringLiteral(":memory:") : path;
    if (m_path == newPath)
        return;

    m_path = newPath;
    emit pathChanged();

    auto db = QSqlDatabase::database(m_uuid, /*open*/ false);
    db.close();
    db.setDatabaseName(newPath);
    db.open();

    QSqlQuery query(db);
    query.exec("CREATE TABLE IF NOT EXISTS frequencies (id TEXT PRIMARY KEY, frequency INTEGER)");

    updateAppFrequencies();
}

QList<QObject*> AppDb::entries() const {
    return m_entries;
}

void AppDb::setEntries(const QList<QObject*>& entries) {
    if (m_entries == entries)
        return;

    m_entries = entries;
    emit entriesChanged();

    // Batch updates to avoid churning.
    m_timer->start();
}

QList<AppEntry*> AppDb::apps() const {
    auto vec = m_apps.values();
    std::sort(vec.begin(), vec.end(), [](AppEntry* a, AppEntry* b) {
        if (a->frequency() != b->frequency())
            return a->frequency() > b->frequency();
        return a->name().localeAwareCompare(b->name()) < 0;
    });
    return vec;
}

void AppDb::incrementFrequency(const QString& id) {
    auto db = QSqlDatabase::database(m_uuid);
    QSqlQuery query(db);

    query.prepare("INSERT INTO frequencies (id, frequency) VALUES (:id, 1) "
                  "ON CONFLICT (id) DO UPDATE SET frequency = frequency + 1");
    query.bindValue(":id", id);
    query.exec();

    for (auto* app : std::as_const(m_apps)) {
        if (app->id() == id) {
            const auto before = apps();
            app->incrementFrequency();
            if (before != apps())
                emit appsChanged();
            return;
        }
    }

    qWarning() << "AppDb::incrementFrequency: could not find app with id" << id;
}

quint32 AppDb::getFrequency(const QString& id) const {
    auto db = QSqlDatabase::database(m_uuid);
    QSqlQuery query(db);

    query.prepare("SELECT frequency FROM frequencies WHERE id = :id");
    query.bindValue(":id", id);

    if (query.exec() && query.next())
        return query.value(0).toUInt();

    return 0;
}

void AppDb::updateAppFrequencies() {
    for (auto* app : std::as_const(m_apps))
        app->setFrequency(getFrequency(app->id()));
}

void AppDb::updateApps() {
    bool dirty = false;

    // Add or refresh
    for (const auto& entry : std::as_const(m_entries)) {
        const auto idVar = entry->property("id");
        const QString id = idVar.toString();
        if (id.isEmpty())
            continue;

        if (!m_apps.contains(id)) {
            dirty = true;
            auto* newEntry = new AppEntry(entry, getFrequency(id), this);
            QObject::connect(newEntry, &QObject::destroyed, this, [this, id]() {
                if (m_apps.remove(id))
                    emit appsChanged();
            });
            m_apps.insert(id, newEntry);
        }
    }

    // Remove missing
    QSet<QString> newIds;
    newIds.reserve(m_entries.size());
    for (const auto& entry : std::as_const(m_entries))
        newIds.insert(entry->property("id").toString());

    for (auto it = m_apps.keyBegin(); it != m_apps.keyEnd();) {
        const QString& id = *it;
        if (!newIds.contains(id)) {
            dirty = true;
            auto* doomed = m_apps.take(id);
            doomed->deleteLater();
            // key iterator invalidated by take(): restart
            it = m_apps.keyBegin();
            continue;
        }
        ++it;
    }

    if (dirty)
        emit appsChanged();
}

} // namespace caelestia
