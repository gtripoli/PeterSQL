# View Options Matrix

Legend: - Supported - Not supported - Supported with differences

------------------------------------------------------------------------

## Common Fields

  -----------------------------------------------------------------------------
  Field       MySQL       MariaDB      PostgreSQL       Oracle      SQLite
  ----------- ----------- ------------ ---------------- ----------- -----------
  Name        Supported   Supported    Supported        Supported   Supported

  SELECT      Supported   Supported    Supported        Supported   Supported
  statement                                                         
  -----------------------------------------------------------------------------

------------------------------------------------------------------------

## Schema

  Field    MySQL     MariaDB   PostgreSQL   Oracle      SQLite
  -------- --------- --------- ------------ ----------- ---------------
  Schema   Partial   Partial   Supported    Supported   Not supported

-   MySQL/MariaDB use database-qualified names (db.view), not true
    schemas like PostgreSQL/Oracle.

------------------------------------------------------------------------

## DEFINER

  --------------------------------------------------------------------------------
  Field          MySQL       MariaDB      PostgreSQL       Oracle      SQLite
  -------------- ----------- ------------ ---------------- ----------- -----------
  DEFINER=user   Supported   Supported    Not supported    Not         Not
                                                           supported   supported

  --------------------------------------------------------------------------------

------------------------------------------------------------------------

## SQL SECURITY

  ----------------------------------------------------------------------------
  Field      MySQL       MariaDB      PostgreSQL       Oracle      SQLite
  ---------- ----------- ------------ ---------------- ----------- -----------
  SQL        Supported   Supported    Not supported    Not         Not
  SECURITY                                             supported   supported
  {DEFINER /                                                       
  INVOKER}                                                         

  ----------------------------------------------------------------------------

------------------------------------------------------------------------

## ALGORITHM

  -----------------------------------------------------------------------------
  Field       MySQL       MariaDB      PostgreSQL       Oracle      SQLite
  ----------- ----------- ------------ ---------------- ----------- -----------
  ALGORITHM   Supported   Supported    Not supported    Not         Not
                                                        supported   supported

  -----------------------------------------------------------------------------

Values: - UNDEFINED - MERGE - TEMPTABLE

------------------------------------------------------------------------

## CHECK OPTION / CONSTRAINT

  ----------------------------------------------------------------------------
  Option     MySQL       MariaDB      PostgreSQL       Oracle      SQLite
  ---------- ----------- ------------ ---------------- ----------- -----------
  WITH CHECK Supported   Supported    Supported        Partial     Not
  OPTION                                                           supported

  LOCAL      Supported   Supported    Supported        Not         Not
                                                       supported   supported

  CASCADED   Supported   Supported    Supported        Not         Not
                                                       supported   supported

  READ ONLY  Not         Not          Not supported    Supported   Not
             supported   supported                                 supported

  CHECK      Not         Not          Not supported    Supported   Not
  OPTION     supported   supported                                 supported
  ONLY                                                             
  ----------------------------------------------------------------------------

Notes: - MySQL/MariaDB/PostgreSQL: WITH \[CASCADED \| LOCAL\] CHECK
OPTION - Oracle: WITH READ ONLY or WITH CHECK OPTION - SQLite: not
supported

------------------------------------------------------------------------

## SECURITY BARRIER

  ------------------------------------------------------------------------------------
  Field              MySQL       MariaDB      PostgreSQL       Oracle      SQLite
  ------------------ ----------- ------------ ---------------- ----------- -----------
  SECURITY_BARRIER   Not         Not          Supported        Not         Not
                     supported   supported                     supported   supported

  ------------------------------------------------------------------------------------

------------------------------------------------------------------------

## FORCE

  ----------------------------------------------------------------------------
  Field      MySQL       MariaDB      PostgreSQL       Oracle      SQLite
  ---------- ----------- ------------ ---------------- ----------- -----------
  FORCE      Not         Not          Not supported    Supported   Not
             supported   supported                                 supported

  ----------------------------------------------------------------------------
