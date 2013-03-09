;; http://www.emacswiki.org/emacs/DirectoryVariables
;; http://stackoverflow.com/questions/4012321/how-can-i-access-the-path-to-the-current-directory-in-an-emacs-directory-variabl
((nil .
      ((eval . (setq qdot/project-directory (locate-dominating-file buffer-file-name ".dir-locals.el")))))
 (python-mode .
	      ((eval .
		     (setq proj-args (list "--sys-path" (expand-file-name "fuckeverything" qdot/project-directory) "--sys-path" qdot/project-directory)))
	       (eval .
		     (set (make-local-variable 'jedi:server-args) proj-args)))))
