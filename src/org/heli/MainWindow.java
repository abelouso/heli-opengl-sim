package org.heli;

import java.awt.Frame;
import java.awt.MenuContainer;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.awt.event.ItemEvent;
import java.awt.event.ItemListener;
import java.awt.event.KeyEvent;
import java.awt.event.KeyListener;
import java.awt.event.WindowAdapter;
import java.awt.event.WindowEvent;

import javax.media.opengl.GL;
import javax.media.opengl.GL2;
import javax.media.opengl.GLAutoDrawable;
import javax.media.opengl.GLEventListener;
import javax.media.opengl.awt.GLCanvas;
import javax.swing.Action;
import javax.swing.JFrame;
import javax.swing.JMenu;
import javax.swing.JMenuBar;
import javax.swing.JMenuItem;
import javax.swing.JPanel;

public class MainWindow extends JFrame implements ActionListener, GLEventListener, ItemListener {

	JMenuBar menuBar;
	JMenu fileMenu;
	JMenuItem fmenuQuit;
	//JMenu displayMenu;
	World theWorld;
	long lastDisplayedTime;

	private int myWidth;
	private int myHeight;
	public MainWindow(World world, String windowTitle, int w, int h, GLCanvas canvas)
	{
		super(windowTitle);
		theWorld = world;
		setSize(w, h);
		myWidth = w;
		myHeight = h;
		add(canvas);
		setVisible(true);
		setFocusable(true);
		lastDisplayedTime = System.nanoTime();
		
		this.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
		/*addWindowListener(new WindowAdapter() {
			public void windowClosing(WindowEvent e) {
				System.exit(0);
			}
		}); */
		menuBar = new JMenuBar();
		fileMenu = new JMenu("File");
		//displayMenu = new JMenu("Display");
		fileMenu.setMnemonic(KeyEvent.VK_F);
		menuBar.add(fileMenu);
		//menuBar.add(displayMenu);
		
		fmenuQuit = new JMenuItem("Quit", KeyEvent.VK_Q);
		fileMenu.add(fmenuQuit);
		fmenuQuit.addActionListener(new ActionListener() {
			public void actionPerformed(ActionEvent event) {
				System.exit(0);
			}
		});
		setJMenuBar(menuBar);
	}

	@Override
	public void itemStateChanged(ItemEvent arg0) {
		// TODO Auto-generated method stub
		
	}

	@Override
	public void actionPerformed(ActionEvent e) {
		// TODO Auto-generated method stub
		
	}

	@Override
	public void display(GLAutoDrawable drawable) {
		render(drawable);
	}

	@Override
	public void dispose(GLAutoDrawable arg0) {
		// TODO Auto-generated method stub
		
	}

	@Override
	public void init(GLAutoDrawable drawable) {
		GL gl = drawable.getGL();
	    GL2 gl2 = gl.getGL2();
	    theWorld.updateCamera(gl2, myWidth, myHeight);
        // Global settings.
    	gl.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA);
        gl.glEnable( GL.GL_BLEND );

        gl.glEnable(GL2.GL_FOG);
        gl2.glFogi(GL2.GL_FOG_MODE, GL2.GL_LINEAR);
        gl2.glHint(GL2.GL_FOG_HINT, GL2.GL_NICEST);
        float fogColor[] = {0.0f, 0.0f, 0.0f, 0.1f };
        gl2.glFogfv( GL2.GL_FOG_COLOR, fogColor, 0 );
        gl2.glFogf(GL2.GL_FOG_START, 0.0f); // Fog Start Depth 
        gl2.glFogf(GL2.GL_FOG_END, 100.0f); // Fog End Depth
        //gl2.glHint(GL2.GL_FOG_HINT, GL2.GL_FASTEST);
        /*
        // TODO: Add options for faster or nicer
        gl2.glFogi( GL2.GL_FOG_COORD_SRC, GL2.GL_FOG_COORD );
        //gl2.glFogi( GL2.GL_FOG_COORD_SRC, GL2.GL_FRAGMENT_DEPTH );
         */

        gl.glEnable(GL.GL_DEPTH_TEST);
        gl.glDepthFunc(GL.GL_LEQUAL);
        //gl2.glShadeModel(GL2.GL_SMOOTH);
        gl2.glShadeModel(GL.GL_SMOOTH_LINE_WIDTH_RANGE);
        gl2.glHint(GL2.GL_PERSPECTIVE_CORRECTION_HINT, GL.GL_NICEST);
        gl.glClearColor(0.0f, 0.0f, 0.0f, 0.0f);
        System.out.println("Initialized the GL Window");
	}

	@Override
	public void reshape(GLAutoDrawable drawable, int x, int y, int w, int h) {
		myWidth = w;
		myHeight = h;
	}
	
	public void render(GLAutoDrawable drawable)
	{
	    theWorld.render(drawable);
	    long currentTime = System.nanoTime();
	    long deltaTime = currentTime - lastDisplayedTime;
	    if (deltaTime > 1000000000)
	    {
	    	this.setTitle("Stigmergy Tick: " + Math.round(theWorld.getTick()));
		    lastDisplayedTime = currentTime;
	    }
	}
}
