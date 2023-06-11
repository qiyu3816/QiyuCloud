create table `qiyu_vocabulary`(
    word_id INT UNSIGNED NOT NULL AUTO_INCREMENT,
    en_word VARCHAR(200) NOT NULL unique,
    chi_val VARCHAR(200) NOT NULL,
    create_time DATE NOT NULL,
    review_time DATE,
    PRIMARY KEY (word_id)
)DEFAULT CHARSET=utf8;