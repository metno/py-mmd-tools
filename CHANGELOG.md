# Changelog

## [v2.2.2](https://github.com/metno/py-mmd-tools/compare/v2.2.1...v2.2.2) - 2024-01-03
- Issue238 creator role by @mortenwh in https://github.com/metno/py-mmd-tools/pull/281
- change heading by @mortenwh in https://github.com/metno/py-mmd-tools/pull/283
- Issue238 creator role by @mortenwh in https://github.com/metno/py-mmd-tools/pull/289
- Remove empty alternate id from MMD xml, and add quality control by @mortenwh in https://github.com/metno/py-mmd-tools/pull/288
- Issue286 license identifier by @mortenwh in https://github.com/metno/py-mmd-tools/pull/287
- Add option to send json input, for use in api py-mmd-tools by @Teddy-1000 in https://github.com/metno/py-mmd-tools/pull/293
- #291: test and solution by @mortenwh in https://github.com/metno/py-mmd-tools/pull/296
- Issue294 ds citation by @mortenwh in https://github.com/metno/py-mmd-tools/pull/295
- Extract standard names from variables in netcdf file and add as CFSTDN keywords by @shamlymajeed in https://github.com/metno/py-mmd-tools/pull/284
- Update tool to use pyproject for setuptools config by @Teddy-1000 in https://github.com/metno/py-mmd-tools/pull/298
- Fix routing to source folder by @Teddy-1000 in https://github.com/metno/py-mmd-tools/pull/300
- Update tagpr.yml by @Teddy-1000 in https://github.com/metno/py-mmd-tools/pull/301

## [v2.2.1](https://github.com/metno/py-mmd-tools/compare/v2.2.0...v2.2.1) - 2023-10-24
- dirty solution to make it compatible with old files  by @charlienegri in https://github.com/metno/py-mmd-tools/pull/280

## [v2.2.0](https://github.com/metno/py-mmd-tools/compare/v2.1.0...v2.2.0) - 2023-10-05
- Fix issue 212 long short names by @charlienegri in https://github.com/metno/py-mmd-tools/pull/269

## [v2.1.0](https://github.com/metno/py-mmd-tools/compare/v2.0.0...v2.1.0) - 2023-08-18
- Issue165 update installation docs by @jo-asplin-met-no in https://github.com/metno/py-mmd-tools/pull/222
- #205: some corrections by @mortenwh in https://github.com/metno/py-mmd-tools/pull/223
- Move script dir into package by @magnusuMET in https://github.com/metno/py-mmd-tools/pull/228
- #234: check for empty string instead of boolean false by @mortenwh in https://github.com/metno/py-mmd-tools/pull/235
- Issue226 cf and netcdf attrs by @mortenwh in https://github.com/metno/py-mmd-tools/pull/233
- #236: parse collection keyword by @mortenwh in https://github.com/metno/py-mmd-tools/pull/237
- #245: added a custom function for operational_status by @mortenwh in https://github.com/metno/py-mmd-tools/pull/246
- #232: require both input file and opendap url unless the user only wa… by @mortenwh in https://github.com/metno/py-mmd-tools/pull/244
- Use search_lowercase for the MMDGroup by @johtoblan in https://github.com/metno/py-mmd-tools/pull/249
- Adds options for wms link and layer names by @TAlonglong in https://github.com/metno/py-mmd-tools/pull/250
- #253: issue warning if invalid url by @mortenwh in https://github.com/metno/py-mmd-tools/pull/254
- Added test and raise an error if not the related_dataset relation par… by @magnarem in https://github.com/metno/py-mmd-tools/pull/251
- Handle acdd attribute project in format "Some Project Name (SPN)" by @TAlonglong in https://github.com/metno/py-mmd-tools/pull/252
- #258: empty platform names ok by @mortenwh in https://github.com/metno/py-mmd-tools/pull/259
- Issue256 return data if namespace missing by @mortenwh in https://github.com/metno/py-mmd-tools/pull/260
- #229: delete README file by @mortenwh in https://github.com/metno/py-mmd-tools/pull/261
- #264: no need for required absolute file path by @mortenwh in https://github.com/metno/py-mmd-tools/pull/265
- Some acdd attributes should follow controlled mmd vocabularies by @shamlymajeed in https://github.com/metno/py-mmd-tools/pull/257
- Added additional naming authorities by @shamlymajeed in https://github.com/metno/py-mmd-tools/pull/270
- Correcting error messages by @shamlymajeed in https://github.com/metno/py-mmd-tools/pull/268
- #274: allow custom dataset citation by @mortenwh in https://github.com/metno/py-mmd-tools/pull/275
- Issue276 repeated ids by @mortenwh in https://github.com/metno/py-mmd-tools/pull/277

## [v2.0.0](https://github.com/metno/py-mmd-tools/compare/v1.1.5...v2.0.0) - 2022-12-13
- Issue #13: Add linting, fix tests and code style by @vkbo in https://github.com/metno/py-mmd-tools/pull/117
- remove unused code for json from ODA by @ElodieFZ in https://github.com/metno/py-mmd-tools/pull/115
- Add script folder to coverage report by @vkbo in https://github.com/metno/py-mmd-tools/pull/120
- #72: updates of translations between ACDD extensions and MMD. This sh… by @mortenwh in https://github.com/metno/py-mmd-tools/pull/108
- Issue118 vagrantfile by @mortenwh in https://github.com/metno/py-mmd-tools/pull/122
- Issue28 script tests by @mortenwh in https://github.com/metno/py-mmd-tools/pull/121
- #95: Changed code and tests for handling missing and invalid id attri… by @mortenwh in https://github.com/metno/py-mmd-tools/pull/124
- #127: use 4 decimals for the polygons by @mortenwh in https://github.com/metno/py-mmd-tools/pull/128
- Issue126 metadata status by @mortenwh in https://github.com/metno/py-mmd-tools/pull/129
- #125: make time_coverage_start required by @mortenwh in https://github.com/metno/py-mmd-tools/pull/131
- #123: added acdd_ext alternate_identifier by @mortenwh in https://github.com/metno/py-mmd-tools/pull/130
- Issue132 date created type by @mortenwh in https://github.com/metno/py-mmd-tools/pull/135
- Issue134 naming authority by @mortenwh in https://github.com/metno/py-mmd-tools/pull/137
- Issue136 alternate identifier type by @mortenwh in https://github.com/metno/py-mmd-tools/pull/139
- Replace pythesint by @johtoblan in https://github.com/metno/py-mmd-tools/pull/140
- Issue107 Remove acdd ext by @johtoblan in https://github.com/metno/py-mmd-tools/pull/141
- Issue142 mmd to nc by @ElodieFZ in https://github.com/metno/py-mmd-tools/pull/143
- #145: updates according to issue description. by @mortenwh in https://github.com/metno/py-mmd-tools/pull/146
- added gemet and northemes keywords and keywords_vocabulary examples by @mortenwh in https://github.com/metno/py-mmd-tools/pull/144
- Issue147 optional checksum by @johtoblan in https://github.com/metno/py-mmd-tools/pull/148
- #151: is this an acceptable solution..? by @mortenwh in https://github.com/metno/py-mmd-tools/pull/152
- #149: nc2mmd fails more gently when missing optional field by @johtoblan in https://github.com/metno/py-mmd-tools/pull/150
- #153: test and updated code by @mortenwh in https://github.com/metno/py-mmd-tools/pull/154
- Moved methods for creating adoc file about ACDD elements from nc_to_m… by @mortenwh in https://github.com/metno/py-mmd-tools/pull/157
- Issue161 logging by @mortenwh in https://github.com/metno/py-mmd-tools/pull/162
- #158: changed the column heading and added that recommended acdd attr… by @mortenwh in https://github.com/metno/py-mmd-tools/pull/159
- Fixed validation problems by @jo-asplin-met-no in https://github.com/metno/py-mmd-tools/pull/170
- #164: now checks format of all times. Also modified the line length o… by @mortenwh in https://github.com/metno/py-mmd-tools/pull/186
- Issue163 long names by @mortenwh in https://github.com/metno/py-mmd-tools/pull/185
- Issue178 license by @mortenwh in https://github.com/metno/py-mmd-tools/pull/183
- #180: properly check the conventions attribute by @mortenwh in https://github.com/metno/py-mmd-tools/pull/184
- #171: removed contributor_organisation as acdd extension, and updated… by @mortenwh in https://github.com/metno/py-mmd-tools/pull/188
- Issue174 valid urls by @mortenwh in https://github.com/metno/py-mmd-tools/pull/190
- #181: check that geospatial coordinates can be converted to float by @mortenwh in https://github.com/metno/py-mmd-tools/pull/189
- Issue179 consistence with adc by @mortenwh in https://github.com/metno/py-mmd-tools/pull/192
- #168: acdd reference attribute used for related information instead o… by @mortenwh in https://github.com/metno/py-mmd-tools/pull/187
- Issue195 get license invalid url by @mortenwh in https://github.com/metno/py-mmd-tools/pull/196
- #194: updated description text by @mortenwh in https://github.com/metno/py-mmd-tools/pull/197
- #199: updated license example and description text in the table. by @mortenwh in https://github.com/metno/py-mmd-tools/pull/200
- #201: added links to MMD and GCMD controlled vocabularies by @mortenwh in https://github.com/metno/py-mmd-tools/pull/202
- Issue203 space in attrs by @mortenwh in https://github.com/metno/py-mmd-tools/pull/204
- Issue206 publisher elems by @mortenwh in https://github.com/metno/py-mmd-tools/pull/207
- #210: improved description of how to use platform and instrument gcmd… by @mortenwh in https://github.com/metno/py-mmd-tools/pull/211
- Issue208 instrument vocab bug by @mortenwh in https://github.com/metno/py-mmd-tools/pull/209
- Issue176 support python versions by @jo-asplin-met-no in https://github.com/metno/py-mmd-tools/pull/193
- #215: bug fix, improved description, and updated test by @mortenwh in https://github.com/metno/py-mmd-tools/pull/216
- #213: changed description text by @mortenwh in https://github.com/metno/py-mmd-tools/pull/214
- Added entry points by @jo-asplin-met-no in https://github.com/metno/py-mmd-tools/pull/217
- Update github actions by @johtoblan in https://github.com/metno/py-mmd-tools/pull/220
- #218: this should make it a little more flexible by @mortenwh in https://github.com/metno/py-mmd-tools/pull/219
- Updated package version by @jo-asplin-met-no in https://github.com/metno/py-mmd-tools/pull/221

## [v1.1.5](https://github.com/metno/py-mmd-tools/compare/1.1.4...v1.1.5) - 2021-08-26
- #91: changed default values by @mortenwh in https://github.com/metno/py-mmd-tools/pull/92
- Issue90 remove xml code by @mortenwh in https://github.com/metno/py-mmd-tools/pull/93
- Issue78 multilingual title abstract by @mortenwh in https://github.com/metno/py-mmd-tools/pull/94
- Issue96 update nc2mmd by @mortenwh in https://github.com/metno/py-mmd-tools/pull/97
- #100: updated according to new decisions by @mortenwh in https://github.com/metno/py-mmd-tools/pull/101
- Issue98 add acdd ext attr by @TAlonglong in https://github.com/metno/py-mmd-tools/pull/99
- install mmd_elements.yaml by @TAlonglong in https://github.com/metno/py-mmd-tools/pull/103
- fix order by @TAlonglong in https://github.com/metno/py-mmd-tools/pull/105

## [1.1.4](https://github.com/metno/py-mmd-tools/compare/1.1.3...1.1.4) - 2021-04-28

## [1.1.3](https://github.com/metno/py-mmd-tools/compare/1.1.2...1.1.3) - 2021-04-28

## [1.1.2](https://github.com/metno/py-mmd-tools/compare/1.1.1...1.1.2) - 2021-04-27

## [1.1.1](https://github.com/metno/py-mmd-tools/compare/1.1.0...1.1.1) - 2021-04-27
- Add pyproject.toml and fix setup.cfg by @vkbo in https://github.com/metno/py-mmd-tools/pull/89

## [1.1.0](https://github.com/metno/py-mmd-tools/compare/1.0.1...1.1.0) - 2021-04-27
- #87: refactored xml_translate method by using xsd_check for validatio… by @mortenwh in https://github.com/metno/py-mmd-tools/pull/88

## [1.0.1](https://github.com/metno/py-mmd-tools/compare/1.0.0...1.0.1) - 2021-04-26

## [1.0.0](https://github.com/metno/py-mmd-tools/commits/1.0.0) - 2021-04-26
- Mmd2csw iso - this PR adds few methods and docs to perfom mmd_to_csw-iso translation by @epifanio in https://github.com/metno/py-mmd-tools/pull/3
- Issue1 ci by @mortenwh in https://github.com/metno/py-mmd-tools/pull/8
- #3 refactoring by @ElodieFZ in https://github.com/metno/py-mmd-tools/pull/6
- Issue4 refactoringtests by @ElodieFZ in https://github.com/metno/py-mmd-tools/pull/7
- Tests and coverage by @ElodieFZ in https://github.com/metno/py-mmd-tools/pull/11
- Xml2xml by @epifanio in https://github.com/metno/py-mmd-tools/pull/14
- Template for PR descriptions by @mortenwh in https://github.com/metno/py-mmd-tools/pull/16
- Test pr template by @mortenwh in https://github.com/metno/py-mmd-tools/pull/19
- Adressing proposed changes by @epifanio in https://github.com/metno/py-mmd-tools/pull/18
- Issue2 odatommd by @ElodieFZ in https://github.com/metno/py-mmd-tools/pull/10
- #29 add script by @ElodieFZ in https://github.com/metno/py-mmd-tools/pull/30
- Issue31 full check by @ElodieFZ in https://github.com/metno/py-mmd-tools/pull/32
- Update ODA personnel element by @ElodieFZ in https://github.com/metno/py-mmd-tools/pull/35
- Add exit 1 when tests fail by @ElodieFZ in https://github.com/metno/py-mmd-tools/pull/38
- Issue20 validate nc by @ElodieFZ in https://github.com/metno/py-mmd-tools/pull/39
- #43: new script and tests to create adoc file from mmd_elements.yaml by @mortenwh in https://github.com/metno/py-mmd-tools/pull/44
- #46: bug fix by @mortenwh in https://github.com/metno/py-mmd-tools/pull/48
- Issue42 mmd mapping by @mortenwh in https://github.com/metno/py-mmd-tools/pull/47
- #49: publication_date is now correct format by @mortenwh in https://github.com/metno/py-mmd-tools/pull/51
- Issue50 storage information by @mortenwh in https://github.com/metno/py-mmd-tools/pull/52
- #55: bug fix by @mortenwh in https://github.com/metno/py-mmd-tools/pull/57
- Issue56 add netcdf-local-path option by @TAlonglong in https://github.com/metno/py-mmd-tools/pull/58
- Issue59 check mmd by @mortenwh in https://github.com/metno/py-mmd-tools/pull/60
- Add .html to thredds urls by @TAlonglong in https://github.com/metno/py-mmd-tools/pull/63
- Issue64 related dataset by @mortenwh in https://github.com/metno/py-mmd-tools/pull/65
- #66: removed mmd namespace in front of relation_type by @mortenwh in https://github.com/metno/py-mmd-tools/pull/67
- #68: removed defaults for temporal and geographic extent, made it pos… by @mortenwh in https://github.com/metno/py-mmd-tools/pull/69
- Issue73 keywords by @mortenwh in https://github.com/metno/py-mmd-tools/pull/74
- #70: Need config.py file to allow for installation by @TAlonglong in https://github.com/metno/py-mmd-tools/pull/71
- reorg title and summary/abstract parsing due to multilang by @TAlonglong in https://github.com/metno/py-mmd-tools/pull/76
- #79: this should solve #79 and fix the title in the dataset citation. by @mortenwh in https://github.com/metno/py-mmd-tools/pull/80
- added a dot at end of sentence by @mortenwh in https://github.com/metno/py-mmd-tools/pull/82
- #84: change acdd_ext for abstract language from abstract_lang to summ… by @mortenwh in https://github.com/metno/py-mmd-tools/pull/85
