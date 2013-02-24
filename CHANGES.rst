=====================
chitwanabm Changelog
=====================

Version 1.5 - 2013/02/24
___________________________
- Store ChitwanABM version module in module __version__
- Minor documentation revisions
- Add functions for modeling NFO change.
- Remove deprecated alternative models for marriage, first birth timing, and 
  migration.
- Remove saving of pickled intialization files.
- Optimize model for speed.
- Update dependencies to run on a default Amazon EC2 instance.
- Add new verification script to verify person agent attributes over course of 
  a model run.
- Update runmodel to allow passing model run ID as a command line parameter 
  (helpful on EC2).

Version 1.4.2 - 2012/09/04
___________________________

- Prepare for Python 3 compatibility: remove ``dict.has_key()`` usage, and 
  check integer division. Added ``from __future__ import division`` where 
  floating point division was needed.
- Fix a bug in schooling code that led to even very old initial agents getting 
  new years of schooling.
- Move stats code (``draw_from_prob_dist``, ``get_probability_index``, etc.) to 
  pyabm.

Version 1.4.2 - 2012/09/04
___________________________

- Fix PyPI homepage so like to pyabm homepage is working.
- Add details to docs.
- Update batch R script to handle cases where results files are missing from 
  some model run folders (due to cancelled or failed runs, for example). Rather 
  than failing, the script will now print a warning and skip each run with a 
  missing result file.
- Change sleep time in ``threaded_batch_run.py`` to 10 seconds instead of 5 to 
  allow more time for writing world files so different threads don't try to 
  write to the same files at the same time.

Version 1.4.1 - 2012/09/03
___________________________

- Add in missing chitwanabm.rst doc file that was accidentally removed from 
  prior release.
- Miscellaneous doc updates.

Version 1.4 - 2012/09/04
_________________________

- Finalize divorce code.
- Fix bug where household was not destroyed properly if it became empty due to 
  the death of the last returning outmigrant.
- Fix KeyError that ocurred when mothers or fathers were excluded from CVFS 
  data (f663ce1ac77c8e2803084b6db9ba1c9a442f0aa9).
- Restructure layout of code to support uploading to PyPI and installation with 
  ``distribute``.
- Many other small improvements and bugfixes. See git log for details.

Version 1.3 - 2012/08/06
_________________________

- Release for PIRE 2012.

Version 1.2 - 2011/09/08
_________________________

- Release for PIRE 2011.

Version 1.1 - 2010/08/11
_________________________

- Release for PIRE 2010.

Version 1.0 - 2009/08/20
_________________________

- Release for PIRE 2009.
