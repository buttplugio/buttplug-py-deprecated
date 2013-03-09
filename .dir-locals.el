;; http://www.emacswiki.org/emacs/DirectoryVariables

((nil .
      ((eval . (setq qdot/project-directory (locate-dominating-file buffer-file-name ".dir-locals.el")))))
 (python-mode .
	      ((eval .
		     (setq proj-args (list "--sys-path" (expand-file-name "fuckeverything" qdot/project-directory) "--sys-path" qdot/project-directory)))
	       (eval .
		     (set (make-local-variable 'jedi:server-args) proj-args)))))
