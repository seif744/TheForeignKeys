-- ============================================================
-- BargainHunters Schema
-- ============================================================

DROP DATABASE IF EXISTS BargainHunters;

CREATE DATABASE IF NOT EXISTS BargainHunters;

USE BargainHunters;
CREATE TABLE users (
                       user_id     INT             NOT NULL AUTO_INCREMENT,
                       name        VARCHAR(100)    NOT NULL,
                       email       VARCHAR(255)    NOT NULL UNIQUE,
                       is_active   BOOLEAN         NOT NULL DEFAULT TRUE,
                       date_joined DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
                       PRIMARY KEY (user_id)
);

-- ------------------------------------------------------------

CREATE TABLE errors (
                        error_id    INT             NOT NULL AUTO_INCREMENT,
                        error_desc  TEXT            NOT NULL,
                        user_id     INT             NOT NULL,
                        PRIMARY KEY (error_id),
                        CONSTRAINT fk_errors_user
                            FOREIGN KEY (user_id) REFERENCES users(user_id)
                                ON DELETE CASCADE -- note a User will never be deleted only deactivated, in thoery this wont have to be used unless somthing big is messed up
);

-- ------------------------------------------------------------

CREATE TABLE feedback (
                          feedback_id INT             NOT NULL AUTO_INCREMENT,
                          content     TEXT            NOT NULL,
                          created_at  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
                          user_id     INT             NOT NULL,
                          PRIMARY KEY (feedback_id),
                          CONSTRAINT fk_feedback_user
                              FOREIGN KEY (user_id) REFERENCES users(user_id)
                                  ON DELETE CASCADE  -- note a User will never be deleted only deactivated, in thoery this wont have to be used unless somthing big is messed up

);

-- ------------------------------------------------------------

CREATE TABLE user_activity (
                               event_id        INT             NOT NULL AUTO_INCREMENT,
                               event_type      VARCHAR(100)    NOT NULL,
                               event_timestamp DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
                               user_id         INT             NOT NULL,
                               PRIMARY KEY (event_id),
                               CONSTRAINT fk_activity_user
                                   FOREIGN KEY (user_id) REFERENCES users(user_id)
                                       ON DELETE CASCADE
);



-- ------------------------------------------------------------

CREATE TABLE categories (
                            cat_id      INT             NOT NULL, -- should be filled in with the coresponding ID from the ebay api
                            cat_name    VARCHAR(255)    NOT NULL,
                            url         VARCHAR(2048)   NOT NULL,
                            is_active   BOOLEAN         NOT NULL DEFAULT TRUE,
                            current_price DECIMAL(10,2) UNSIGNED ,
                            PRIMARY KEY (cat_id)
);

-- ------------------------------------------------------------

CREATE TABLE items (
                       item_id     INT             NOT NULL , -- should be filled in with the coresponding ID from the ebay api
                       item_name   VARCHAR(255)    NOT NULL,
                       url         VARCHAR(2048)   NOT NULL,
                       is_active   BOOLEAN         NOT NULL DEFAULT TRUE,
                       current_price DECIMAL(10,2) UNSIGNED ,
                    PRIMARY KEY (item_id)

);

-- ------------------------------------------------------------

CREATE TABLE listings (
                          listing_id     INT             NOT NULL, -- should be filled in with the coresponding ID from the ebay api
                          listing_name   VARCHAR(255)    NOT NULL,
                          url         VARCHAR(2048)   NOT NULL,
                          is_active   BOOLEAN         NOT NULL DEFAULT TRUE,
                        current_price DECIMAL(10,2) UNSIGNED ,
                              PRIMARY KEY (listing_id)

);

-- ------------------------------------------------------------

CREATE TABLE watchlist (

                           last_checked    DATETIME,
                           user_id         INT         NOT NULL,
                           alert_id        INT         NOT NULL,
                           PRIMARY KEY (user_id,alert_id),
                           CONSTRAINT fk_watchlist_user
                               FOREIGN KEY (user_id) REFERENCES users(user_id)
                                   ON DELETE CASCADE,
                           CONSTRAINT fk_watchlist_alert
                               FOREIGN KEY (alert_id) REFERENCES alerts(alert_id)
                                   ON DELETE CASCADE

);

-- ------------------------------------------------------------


CREATE TABLE alerts (
                        alert_id        INT             NOT NULL AUTO_INCREMENT,
                        watch_type      ENUM('item', 'category', 'listing') NOT NULL,
                        date_started    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
                        date_ended      DATETIME,
                        is_active       BOOLEAN         NOT NULL DEFAULT TRUE,
                        drop_amt        DECIMAL(10, 2),
                        drop_percent    DECIMAL(5, 2),
                        watchlist_id    INT             NOT NULL,
                        item_id         INT,                       -- FK: nullable — alert targets item OR category OR listing
                        cat_id          INT,                       -- FK: nullable — alert targets item OR category OR listing
                        listing_id      INT,                       -- FK: nullable — alert targets item OR category OR listing
                        PRIMARY KEY (alert_id),
                        CONSTRAINT fk_alerts_watchlist
                            FOREIGN KEY (watchlist_id) REFERENCES watchlist(watchlist_id)
                                ON DELETE CASCADE,
                        CONSTRAINT fk_alerts_item
                            FOREIGN KEY (item_id) REFERENCES items(item_id)
                                ON DELETE SET NULL,
                        CONSTRAINT fk_alerts_category
                            FOREIGN KEY (cat_id) REFERENCES categories(cat_id)
                                ON DELETE SET NULL,
                        CONSTRAINT fk_alerts_listing
                            FOREIGN KEY (listing_id) REFERENCES listings(listing_id)
                                ON DELETE SET NULL

);


-- ------------------------------------------------------------

CREATE TABLE notifications (
                               notification_id INT             NOT NULL AUTO_INCREMENT,
                               content         TEXT            NOT NULL,
                               sent_date       DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
                               user_id         INT             NOT NULL,
                               alert_id        INT             NOT NULL,
                               PRIMARY KEY (notification_id),
                               CONSTRAINT fk_notif_user
                                   FOREIGN KEY (user_id) REFERENCES users(user_id)
                                       ON DELETE CASCADE,
                               CONSTRAINT fk_notif_alert
                                   FOREIGN KEY (alert_id) REFERENCES alerts(alert_id)
                                       ON DELETE CASCADE
);